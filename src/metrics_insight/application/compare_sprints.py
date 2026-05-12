from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.metrics_insight.domain.repository_interfaces import GitHubRepository, MetricsExporter
from src.metrics_insight.domain.metrics_service import MetricsService


class CompareSprints:
    """Use case to compare metrics across multiple time windows (sprints)."""

    def __init__(self, github_repo: GitHubRepository, exporter: MetricsExporter):
        self.github_repo = github_repo
        self.exporter = exporter
        self.metrics_service = MetricsService()

    def execute(
        self, repo_name: str, start_date: datetime, sprint_weeks: int, num_sprints: int, output_path: str
    ) -> List[Dict[str, Any]]:
        """
        Compares N sprints starting from start_date.
        """
        sprint_results = []
        current_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(num_sprints):
            current_end = current_start + timedelta(weeks=sprint_weeks)
            
            prs = self.github_repo.get_pull_requests(repo_name, current_start, current_end)
            if prs:
                metrics_obj = self.metrics_service.calculate_group_metrics(prs, f"Sprint {i + 1}")
                
                metrics = metrics_obj.to_dict()
                metrics["start_date"] = current_start.isoformat()
                metrics["end_date"] = current_end.isoformat()
                sprint_results.append(metrics)
            
            current_start = current_end
            
        return sprint_results
