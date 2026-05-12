from datetime import datetime
from typing import Dict, Any
from src.metrics_insight.domain.repository_interfaces import GitHubRepository

class GetWorkflowMetrics:
    """Use case to fetch and process GitHub Actions workflow runs metrics."""

    def __init__(self, github_repo: GitHubRepository):
        self._github_repo = github_repo

    def execute(self, repo_full_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Fetches workflow runs and calculates execution time statistics.
        """
        runs = self._github_repo.get_workflow_runs(repo_full_name, start_date, end_date)
        
        if not runs:
            return {
                "total_runs": 0,
                "avg_duration_seconds": 0.0,
                "success_rate": 0.0,
                "runs": []
            }

        completed_runs = [r for r in runs if r.status == "completed" and r.duration is not None]
        total_duration = sum(r.duration_seconds for r in completed_runs)
        avg_duration = total_duration / len(completed_runs) if completed_runs else 0.0
        
        successful_runs = [r for r in completed_runs if r.conclusion == "success"]
        success_rate = (len(successful_runs) / len(completed_runs) * 100) if completed_runs else 0.0

        return {
            "total_runs": len(runs),
            "completed_runs": len(completed_runs),
            "avg_duration_seconds": avg_duration,
            "success_rate": success_rate,
            "runs": [
                {
                    "id": r.id,
                    "name": r.name,
                    "status": r.status,
                    "conclusion": r.conclusion,
                    "duration_seconds": r.duration_seconds,
                    "created_at": r.created_at.isoformat(),
                    "html_url": r.html_url
                }
                for r in runs
            ]
        }
