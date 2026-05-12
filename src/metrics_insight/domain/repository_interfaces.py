from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from src.metrics_insight.domain.pull_request import PullRequest
from src.metrics_insight.domain.workflow import WorkflowRun


@dataclass(frozen=True)
class ExportResult:
    """Represents the results to be exported."""
    repo_name: str
    start_date: datetime
    end_date: datetime
    prs: List[PullRequest]
    team_metrics: Dict[str, Any]
    individual_metrics: List[Dict[str, Any]]
    label_metrics: List[Dict[str, Any]]


class GitHubRepository(ABC):
    """Port defining the interface for GitHub data extraction."""

    @abstractmethod
    def get_pull_requests(
        self, repo_full_name: str, start_date: datetime, end_date: datetime
    ) -> List[PullRequest]:
        """
        Fetches pull requests from a repository within a specific date range.
        Dates must be UTC.
        """
        pass

    @abstractmethod
    def get_workflow_runs(
        self, repo_full_name: str, start_date: datetime, end_date: datetime
    ) -> List[WorkflowRun]:
        """
        Fetches workflow runs from a repository within a specific date range.
        Dates must be UTC.
        """
        pass


class SentimentAnalyzer(ABC):
    """Port defining the interface for sentiment analysis of review comments."""

    @abstractmethod
    def analyze_sentiment(self, comments: List[str]) -> Dict[str, Any]:
        """
        Analyzes the sentiment of a list of comments.
        Returns a dictionary with sentiment scores and potential friction detection.
        """
        pass


class RootCauseAnalyzer(ABC):
    """Port defining the interface for AI-driven root cause analysis of metrics."""

    @abstractmethod
    def suggest_root_causes(self, metrics_data: Dict[str, Any], insights: List[Any]) -> str:
        """
        Analyzes metrics and existing insights to suggest potential root causes.
        Returns a string with the AI analysis.
        """
        pass


class PredictiveAnalyzer(ABC):
    """Port defining the interface for AI-driven predictive analysis of PRs."""

    @abstractmethod
    def predict_pr_outcomes(self, pr_data: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Estimates PR duration and rework risk based on current data and history.
        """
        pass


class MetricsExporter(ABC):
    """Port defining the interface for exporting metrics and data."""

    @abstractmethod
    def export(self, result: ExportResult, output_path: str) -> None:
        """Exports all metrics and data to the specified output path."""
        pass
