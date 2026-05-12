import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from src.metrics_insight.infrastructure.cli.main import cli
from src.metrics_insight.application.calculate_metrics import CalculationResult, PRPrediction
from src.metrics_insight.domain.metrics_service import GroupMetrics


class TestFetchCommandAcceptance:
    """
    Acceptance tests for the 'fetch' command.
    Verifies the end-to-end CLI flow by mocking the application layer.
    """

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_bootstrap(self):
        with patch("src.metrics_insight.infrastructure.cli.main._container") as mock:
            yield mock

    def test_fetch_command_success(self, runner, mock_bootstrap):
        repo = "owner/repo"
        start = "2024-01-01"
        end = "2024-01-31"
        
        mock_team_metrics = MagicMock(spec=GroupMetrics)
        mock_team_metrics.total_prs = 5
        mock_team_metrics.jira_percentage = 100.0
        mock_team_metrics.metrics = {}
        
        mock_result = MagicMock(spec=CalculationResult)
        mock_result.team_metrics = mock_team_metrics
        mock_result.predictions = [
            PRPrediction(number=1, title="Test PR", estimated_duration_h=2.5, rework_risk_label="Low", risk_factors=[])
        ]
        mock_result.sentiment = {"sentiment_label": "Positive", "sentiment_score": 0.8, "summary": "Great team spirit."}
        mock_result.ai_analysis = "Team is performing well."
        mock_result.insights = []

        mock_use_case = MagicMock()
        mock_use_case.execute.return_value = mock_result
        mock_bootstrap.get_calculate_metrics.return_value = mock_use_case
        mock_bootstrap.ai_adapter = MagicMock() # Enable AI logs

        result = runner.invoke(cli, ["fetch", "--repo", repo, "--start", start, "--end", end])

        assert result.exit_code == 0
        assert f"Fetching metrics for {repo}" in result.output
        assert "AI Analysis enabled" in result.output
        assert "Success!" in result.output
        assert "Team Summary: owner/repo" in result.output
        assert "Total PRs" in result.output
        assert "AI Predictive Analysis" in result.output
        assert "Overall Sentiment:" in result.output
        
        expected_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        expected_end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        mock_use_case.execute.assert_called_once_with(repo, expected_start, expected_end, "./output")

    def test_fetch_command_invalid_date(self, runner, mock_bootstrap):
        result = runner.invoke(cli, ["fetch", "--repo", "owner/repo", "--start", "invalid", "--end", "2024-01-31"])

        assert result.exit_code == 0
        assert "Error: Invalid date format" in result.output

    def test_fetch_command_bootstrap_failure(self, runner):
        # Simulate _container being None (bootstrap failure)
        with patch("src.metrics_insight.infrastructure.cli.main._container", None):
            result = runner.invoke(cli, ["fetch", "--repo", "owner/repo", "--start", "2024-01-01", "--end", "2024-01-31"])
            
        assert "Error: Bootstrap failed" in result.output
