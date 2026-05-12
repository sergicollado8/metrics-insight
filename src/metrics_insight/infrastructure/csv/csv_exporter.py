import os
import pandas as pd
from typing import List
from src.metrics_insight.domain.pull_request import PullRequest
from src.metrics_insight.domain.repository_interfaces import MetricsExporter, ExportResult
from src.metrics_insight.domain.business_hours import BusinessHoursCalculator


class CSVExporter(MetricsExporter):
    """Adapter for exporting data to CSV files."""

    def export(self, result: ExportResult, output_path: str) -> None:
        """Exports all metrics and data to the specified output path."""
        safe_repo = result.repo_name.replace("/", "_").replace("..", "_")
        
        base_dir = os.path.abspath(output_path)
        repo_dir = os.path.join(base_dir, safe_repo)
        
        try:
            os.makedirs(repo_dir, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Could not create output directory {repo_dir}: {e}")
        
        start_str = result.start_date.strftime("%Y%m%d")
        end_str = result.end_date.strftime("%Y%m%d")
        file_prefix = f"{start_str}_{end_str}"
        path_prefix = os.path.join(repo_dir, file_prefix)

        self._save_raw_pull_requests(result.prs, f"{path_prefix}_raw_prs.csv")

        pd.DataFrame([result.team_metrics]).to_csv(f"{path_prefix}_team.csv", index=False)
        
        pd.DataFrame(result.individual_metrics).to_csv(f"{path_prefix}_individual.csv", index=False)

        if result.label_metrics:
            pd.DataFrame(result.label_metrics).to_csv(f"{path_prefix}_labels.csv", index=False)

    def _save_raw_pull_requests(self, prs: List[PullRequest], path: str) -> None:
        """Saves each PR as a row in a CSV file."""
        data = []
        for pr in prs:
            first_review = pr.first_human_review
            
            lifetime_h = 0.0
            if pr.merged_at:
                lifetime_h = BusinessHoursCalculator.calculate_duration_h(pr.created_at, pr.merged_at)
            
            tt_first_review_h = 0.0
            if first_review:
                tt_first_review_h = BusinessHoursCalculator.calculate_duration_h(pr.created_at, first_review.submitted_at)

            data.append({
                "number": pr.number,
                "title": pr.title,
                "author": pr.author,
                "created_at": pr.created_at.isoformat(),
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else "",
                "size": pr.size,
                "lifetime_h": round(lifetime_h, 2),
                "time_to_first_review_h": round(tt_first_review_h, 2),
                "waiting_for_reviewer_h": round(pr.waiting_for_reviewer_h, 2),
                "waiting_for_author_h": round(pr.waiting_for_author_h, 2),
                "rework_commits": pr.commits_after_first_review,
                "rework_loops": pr.rework_count,
                "jira_ticket": pr.jira_ticket or "",
                "labels": ",".join(pr.labels),
                "author_comments": pr.author_comments_count,
                "bot_comments": pr.bot_comments_count,
                "other_human_comments": pr.other_human_comments_count,
                "first_human_review_at": first_review.submitted_at.isoformat() if first_review else "",
                "first_human_review_by": first_review.author if first_review else ""
            })
        
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
