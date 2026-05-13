import re
import concurrent.futures
from datetime import datetime, timezone
from typing import List, Optional
from github import Github, PullRequest as PyGithubPullRequest
from metrics_insight.domain.pull_request import PullRequest, Review
from metrics_insight.domain.workflow import WorkflowRun
from metrics_insight.domain.repository_interfaces import GitHubRepository


class PyGithubAdapter(GitHubRepository):
    """Adapter for fetching data from GitHub using PyGithub."""

    BOT_IDENTIFIERS = {"bot", "gemini-code-assist", "github-actions", "dependabot"}
    JIRA_PATTERN = r"[A-Z]{2,}-\d+"
    MAX_WORKERS = 10

    def __init__(self, token: str):
        self._github = Github(token, per_page=100)

    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        """Return a timezone-aware datetime in UTC."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def get_pull_requests(
        self, repo_full_name: str, start_date: datetime, end_date: datetime
    ) -> List[PullRequest]:
        repo = self._github.get_repo(repo_full_name)
        start_date = self._ensure_utc(start_date)
        end_date = self._ensure_utc(end_date)

        github_prs = repo.get_pulls(state="closed", sort="updated", direction="desc")
        
        target_gprs: List[PyGithubPullRequest.PullRequest] = []
        for gpr in github_prs:
            if gpr.merged_at:
                merged_at_utc = self._ensure_utc(gpr.merged_at)
                if start_date <= merged_at_utc <= end_date:
                    target_gprs.append(gpr)
            
            if self._ensure_utc(gpr.updated_at) < start_date:
                break
        
        domain_prs: List[PullRequest] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            future_to_pr = {executor.submit(self._to_domain, gpr): gpr for gpr in target_gprs}
            for future in concurrent.futures.as_completed(future_to_pr):
                try:
                    domain_prs.append(future.result())
                except Exception as exc:
                    print(f"PR detail fetch generated an exception: {exc}")
                
        return sorted(domain_prs, key=lambda x: x.merged_at if x.merged_at else x.created_at, reverse=True)

    def get_workflow_runs(
        self, repo_full_name: str, start_date: datetime, end_date: datetime
    ) -> List[WorkflowRun]:
        repo = self._github.get_repo(repo_full_name)
        start_date = self._ensure_utc(start_date)
        end_date = self._ensure_utc(end_date)

        runs = repo.get_workflow_runs()
        
        target_runs: List[WorkflowRun] = []
        for run in runs:
            created_at = self._ensure_utc(run.created_at)
            
            if created_at > end_date:
                continue
            
            if created_at < start_date:
                break
                
            updated_at = self._ensure_utc(run.updated_at)
            
            started_at = getattr(run, "run_started_at", run.created_at)
            if started_at:
                started_at = self._ensure_utc(started_at)
            
            duration = None
            if run.status == "completed" and started_at and updated_at:
                duration = updated_at - started_at

            target_runs.append(WorkflowRun(
                id=run.id,
                name=run.name or "Unknown",
                status=run.status,
                conclusion=run.conclusion,
                created_at=created_at,
                updated_at=updated_at,
                started_at=started_at,
                completed_at=updated_at if run.status == "completed" else None,
                duration=duration,
                html_url=run.html_url
            ))
            
        return target_runs

    def _to_domain(self, gpr: PyGithubPullRequest.PullRequest) -> PullRequest:
        reviews = self._get_reviews(gpr)
        author_login = gpr.user.login
        first_review = self._find_first_human_review(reviews, author_login)
        
        rework_commits = 0
        rework_events = 0
        last_commit_at = None
        first_rework_at = None
        
        commits = list(gpr.get_commits())
        if commits:
            last_commit_at = self._ensure_utc(commits[-1].commit.author.date)
            
        if first_review:
            rework_commits = self._count_rework_commits(commits, first_review.submitted_at)
            rework_events = 1 if rework_commits > 0 else 0
            first_rework_at = self._find_first_rework_at(commits, reviews, first_review.submitted_at, author_login)

        review_requested_at = self._ensure_utc(gpr.created_at)
        
        jira_ticket = self._extract_jira_ticket(gpr.title, gpr.body or "")
        labels = [label.name for label in gpr.labels]
        ready_for_review_date = None
        for event in gpr.get_issue_events():
            if event.event == "ready_for_review":
                ready_for_review_date = event.created_at
                break

        author_comments = 0
        bot_comments = 0
        other_human_comments = 0

        for rc in gpr.get_review_comments():
            is_bot = rc.user.type == "Bot" or any(bot in rc.user.login.lower() for bot in self.BOT_IDENTIFIERS)
            if is_bot:
                bot_comments += 1
            elif rc.user.login == author_login:
                author_comments += 1
            else:
                other_human_comments += 1

        for ic in gpr.get_issue_comments():
            is_bot = ic.user.type == "Bot" or any(bot in ic.user.login.lower() for bot in self.BOT_IDENTIFIERS)
            if is_bot:
                bot_comments += 1
            elif ic.user.login == author_login:
                author_comments += 1
            else:
                other_human_comments += 1

        return PullRequest(
            number=gpr.number,
            title=gpr.title,
            author=gpr.user.login,
            created_at=self._ensure_utc(ready_for_review_date or gpr.created_at),
            merged_at=self._ensure_utc(gpr.merged_at) if gpr.merged_at else None,
            closed_at=self._ensure_utc(gpr.closed_at) if gpr.closed_at else None,
            additions=gpr.additions,
            deletions=gpr.deletions,
            labels=labels,
            reviews=reviews,
            commits_after_first_review=rework_commits,
            rework_count=rework_events,
            jira_ticket=jira_ticket,
            review_requested_at=review_requested_at,
            last_commit_at=last_commit_at,
            first_rework_at=first_rework_at,
            author_comments_count=author_comments,
            bot_comments_count=bot_comments,
            other_human_comments_count=other_human_comments
        )

    def _get_reviews(self, gpr: PyGithubPullRequest.PullRequest) -> List[Review]:
        domain_reviews = []
        for r in gpr.get_reviews():
            is_bot = r.user.type == "Bot" or any(bot in r.user.login.lower() for bot in self.BOT_IDENTIFIERS)
            submitted_at = self._ensure_utc(r.submitted_at) if r.submitted_at else None
            if submitted_at:
                domain_reviews.append(Review(
                    submitted_at=submitted_at,
                    author=r.user.login,
                    is_bot=is_bot,
                    body=r.body
                ))
        return domain_reviews

    def _find_first_human_review(self, reviews: List[Review], author_login: str) -> Optional[Review]:
        human_reviews = [r for r in reviews if not r.is_bot and r.author != author_login]
        if not human_reviews:
            return None
        return min(human_reviews, key=lambda r: r.submitted_at)

    def _find_first_rework_at(self, commits: list, reviews: List[Review], first_review_at: datetime, author: str) -> Optional[datetime]:
        first_rework_at = None
        
        for commit in commits:
            commit_date = self._ensure_utc(commit.commit.author.date)
            if commit_date > first_review_at:
                if not self._is_merge(commit.commit.message.lower()):
                    if first_rework_at is None or commit_date < first_rework_at:
                        first_rework_at = commit_date
        
        for r in reviews:
            if r.author == author and r.submitted_at > first_review_at:
                if first_rework_at is None or r.submitted_at < first_rework_at:
                    first_rework_at = r.submitted_at
                    
        return first_rework_at

    def _count_rework_commits(self, commits: list, first_review_at: datetime) -> int:
        rework_count = 0
        for commit in commits:
            commit_date = self._ensure_utc(commit.commit.author.date)
            if commit_date > first_review_at:
                if not self._is_merge(commit.commit.message.lower()):
                    rework_count += 1
        return rework_count

    @staticmethod
    def _is_merge(msg) -> bool:
        return "merge branch" in msg or "merge pull request" in msg or "merge remote-tracking" in msg

    def _extract_jira_ticket(self, title: str, body: str) -> Optional[str]:
        matches = re.findall(self.JIRA_PATTERN, f"{title} {body}")
        return matches[0] if matches else None
