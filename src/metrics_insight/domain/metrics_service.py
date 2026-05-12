from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from src.metrics_insight.domain.pull_request import PullRequest
from src.metrics_insight.domain.metrics import MetricCalculator, AggregatedMetric
from src.metrics_insight.domain.business_hours import BusinessHoursCalculator


@dataclass(frozen=True)
class GroupMetrics:
    """Metrics for a specific group (Team, Individual, or Label)."""
    label: str
    total_prs: int
    prs_with_jira: int
    prs_without_jira: int
    jira_percentage: float
    metrics: Dict[str, Optional[AggregatedMetric]]

    def to_dict(self) -> Dict[str, Any]:
        """Flattens the metrics into a dictionary for export."""
        result = {
            "label": self.label,
            "total_prs": self.total_prs,
            "prs_with_jira": self.prs_with_jira,
            "prs_without_jira": self.prs_without_jira,
            "jira_percentage": self.jira_percentage,
        }
        
        for name, agg in self.metrics.items():
            if not agg:
                result.update({f"{name}_{k}": 0.0 for k in ["min", "avg", "median", "p85", "max"]})
            else:
                result.update({
                    f"{name}_min": agg.min,
                    f"{name}_avg": agg.average,
                    f"{name}_median": agg.median,
                    f"{name}_p85": agg.p85,
                    f"{name}_max": agg.max,
                })
        
        return result


class MetricsService:
    """Domain service for aggregating metrics across different dimensions."""

    def calculate_team_metrics(self, prs: List[PullRequest]) -> GroupMetrics:
        return self.calculate_group_metrics(prs, "Team")

    def calculate_individual_metrics(self, prs: List[PullRequest]) -> List[GroupMetrics]:
        authors = sorted(list(set(pr.author for pr in prs)))
        return [
            self.calculate_group_metrics([pr for pr in prs if pr.author == author], author)
            for author in authors
        ]

    def calculate_label_metrics(self, prs: List[PullRequest]) -> List[GroupMetrics]:
        labels: Set[str] = set()
        for pr in prs:
            labels.update(pr.labels)
        
        sorted_labels = sorted(list(labels))
        return [
            self.calculate_group_metrics([pr for pr in prs if label in pr.labels], f"Label: {label}")
            for label in sorted_labels
        ]

    def calculate_group_metrics(self, prs: List[PullRequest], label: str) -> GroupMetrics:
        sizes = [float(pr.size) for pr in prs]
        lifetimes = []
        tt_first_reviews = []
        waiting_reviewer = []
        waiting_author = []
        rework_commits = [float(pr.commits_after_first_review) for pr in prs]
        rework_loops = [float(pr.rework_count) for pr in prs]
        
        prs_with_jira = 0
        
        for pr in prs:
            if pr.has_jira_ticket:
                prs_with_jira += 1
            
            if pr.merged_at:
                lifetimes.append(BusinessHoursCalculator.calculate_duration_h(pr.created_at, pr.merged_at))
                waiting_reviewer.append(pr.waiting_for_reviewer_h)
                waiting_author.append(pr.waiting_for_author_h)
            
            first_review = pr.first_human_review
            if first_review:
                tt_first_reviews.append(
                    BusinessHoursCalculator.calculate_duration_h(pr.created_at, first_review.submitted_at)
                )

        total_prs = len(prs)
        jira_percentage = (prs_with_jira / total_prs * 100) if total_prs > 0 else 0

        metrics = {
            "pr_size": MetricCalculator.calculate_aggregates(sizes),
            "pr_lifetime_h": MetricCalculator.calculate_aggregates(lifetimes),
            "time_to_first_review_h": MetricCalculator.calculate_aggregates(tt_first_reviews),
            "waiting_for_reviewer_h": MetricCalculator.calculate_aggregates(waiting_reviewer),
            "waiting_for_author_h": MetricCalculator.calculate_aggregates(waiting_author),
            "rework_commits": MetricCalculator.calculate_aggregates(rework_commits),
            "rework_loops": MetricCalculator.calculate_aggregates(rework_loops),
        }

        return GroupMetrics(
            label=label,
            total_prs=total_prs,
            prs_with_jira=prs_with_jira,
            prs_without_jira=total_prs - prs_with_jira,
            jira_percentage=jira_percentage,
            metrics=metrics
        )
