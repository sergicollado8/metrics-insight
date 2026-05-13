from unittest.mock import MagicMock
from datetime import datetime, timezone
from metrics_insight.application.calculate_metrics import CalculateMetrics
from metrics_insight.domain.pull_request import PullRequest


def test_calculate_metrics_orchestration():
    """Verify that CalculateMetrics use case correctly orchestrates fetching and exporting."""
    # Mock ports
    repo_mock = MagicMock()
    exporter_mock = MagicMock()
    
    # Setup test data
    t1 = datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc)
    prs = [
        PullRequest(number=1, title="PR 1", author="alice", created_at=t1, labels=["area/backend"]),
        PullRequest(number=2, title="PR 2", author="bob", created_at=t1, labels=["area/frontend"])
    ]
    repo_mock.get_pull_requests.return_value = prs
    
    # Run use case
    use_case = CalculateMetrics(repo_mock, exporter_mock)
    result = use_case.execute("owner/repo", t1, t1, "/tmp/output")
    
    # Assertions
    repo_mock.get_pull_requests.assert_called_once()
    exporter_mock.export.assert_called_once()
    
    # Verify the result object
    assert result.repo_name == "owner/repo"
    assert len(result.prs) == 2
    assert len(result.individual_metrics) == 2
    assert len(result.label_metrics) == 2
    
    # Verify data passed to exporter
    export_data = exporter_mock.export.call_args[0][0]
    assert export_data.repo_name == "owner/repo"
    assert len(export_data.prs) == 2
    assert len(export_data.individual_metrics) == 2
    assert len(export_data.label_metrics) == 2
