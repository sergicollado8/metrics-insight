from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from metrics_insight.application.get_workflow_metrics import GetWorkflowMetrics
from metrics_insight.domain.workflow import WorkflowRun


def test_get_workflow_metrics_execute():
    # Arrange
    mock_repo = MagicMock()
    start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2023, 1, 31, tzinfo=timezone.utc)
    
    run1 = WorkflowRun(
        id=1, name="CI", status="completed", conclusion="success",
        created_at=start_date, updated_at=start_date + timedelta(minutes=10),
        started_at=start_date, completed_at=start_date + timedelta(minutes=10),
        duration=timedelta(minutes=10), html_url="http://url1"
    )
    run2 = WorkflowRun(
        id=2, name="Deploy", status="completed", conclusion="failure",
        created_at=start_date, updated_at=start_date + timedelta(minutes=20),
        started_at=start_date, completed_at=start_date + timedelta(minutes=20),
        duration=timedelta(minutes=20), html_url="http://url2"
    )
    
    mock_repo.get_workflow_runs.return_value = [run1, run2]
    
    use_case = GetWorkflowMetrics(mock_repo)
    
    # Act
    result = use_case.execute("owner/repo", start_date, end_date)
    
    # Assert
    assert result["total_runs"] == 2
    assert result["completed_runs"] == 2
    assert result["avg_duration_seconds"] == 15 * 60  # (10 + 20) / 2 * 60
    assert result["success_rate"] == 50.0
    assert len(result["runs"]) == 2
    mock_repo.get_workflow_runs.assert_called_once_with("owner/repo", start_date, end_date)

def test_get_workflow_metrics_no_runs():
    # Arrange
    mock_repo = MagicMock()
    mock_repo.get_workflow_runs.return_value = []
    use_case = GetWorkflowMetrics(mock_repo)
    
    # Act
    result = use_case.execute("owner/repo", datetime.now(), datetime.now())
    
    # Assert
    assert result["total_runs"] == 0
    assert result["avg_duration_seconds"] == 0.0
    assert result["success_rate"] == 0.0
    assert result["runs"] == []
