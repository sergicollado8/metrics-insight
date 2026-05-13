import os
from metrics_insight.application.calculate_metrics import CalculateMetrics
from metrics_insight.application.compare_sprints import CompareSprints
from metrics_insight.application.get_workflow_metrics import GetWorkflowMetrics
from metrics_insight.infrastructure.github.github_adapter import PyGithubAdapter
from metrics_insight.infrastructure.csv.csv_exporter import CSVExporter
from metrics_insight.infrastructure.ai.gemini_adapter import GeminiAIAdapter


class Bootstrap:
    """
    Handles Dependency Injection for the Metrics Insight application.
    Centralizes the wiring of infrastructure adapters to application use cases.
    """

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required.")

        self.github_repo = PyGithubAdapter(self.github_token)
        self.exporter = CSVExporter()
        
        self.ai_adapter = None
        if self.gemini_api_key:
            self.ai_adapter = GeminiAIAdapter(self.gemini_api_key)

    def get_calculate_metrics(self) -> CalculateMetrics:
        """Returns the CalculateMetrics use case with injected dependencies."""
        return CalculateMetrics(
            github_repo=self.github_repo,
            exporter=self.exporter,
            sentiment_analyzer=self.ai_adapter,
            root_cause_analyzer=self.ai_adapter,
            predictive_analyzer=self.ai_adapter
        )

    def get_compare_sprints(self) -> CompareSprints:
        """Returns the CompareSprints use case with injected dependencies."""
        return CompareSprints(
            github_repo=self.github_repo,
            exporter=self.exporter
        )

    def get_workflow_metrics(self) -> GetWorkflowMetrics:
        """Returns the GetWorkflowMetrics use case with injected dependencies."""
        return GetWorkflowMetrics(
            github_repo=self.github_repo
        )


def bootstrap() -> Bootstrap:
    """Factory function to create and return the Bootstrap container."""
    return Bootstrap()
