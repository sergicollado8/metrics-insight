from datetime import datetime, timezone
from src.metrics_insight.domain.pull_request import PullRequest
from src.metrics_insight.domain.metrics_service import MetricsService


def test_calculate_team_metrics():
    """Verify that team metrics are correctly aggregated."""
    t1 = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    prs = [
        PullRequest(number=1, title="PR 1", author="alice", created_at=t1, additions=100),
        PullRequest(number=2, title="PR 2", author="bob", created_at=t1, additions=200)
    ]
    
    service = MetricsService()
    result = service.calculate_team_metrics(prs)
    
    assert result.label == "Team"
    assert result.total_prs == 2
    assert result.metrics["pr_size"].average == 150.0
    assert result.metrics["pr_size"].min == 100.0
    assert result.metrics["pr_size"].max == 200.0


def test_calculate_individual_metrics():
    """Verify that individual metrics are correctly grouped and aggregated."""
    t1 = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    prs = [
        PullRequest(number=1, title="PR 1", author="alice", created_at=t1, additions=100),
        PullRequest(number=2, title="PR 2", author="bob", created_at=t1, additions=200),
        PullRequest(number=3, title="PR 3", author="alice", created_at=t1, additions=300)
    ]
    
    service = MetricsService()
    results = service.calculate_individual_metrics(prs)
    
    assert len(results) == 2
    
    # Sorted by author
    alice_metrics = results[0]
    bob_metrics = results[1]
    
    assert alice_metrics.label == "alice"
    assert alice_metrics.total_prs == 2
    assert alice_metrics.metrics["pr_size"].average == 200.0
    
    assert bob_metrics.label == "bob"
    assert bob_metrics.total_prs == 1
    assert bob_metrics.metrics["pr_size"].average == 200.0


def test_calculate_label_metrics():
    """Verify that label-based metrics are correctly grouped and aggregated."""
    t1 = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    prs = [
        PullRequest(number=1, title="PR 1", author="alice", created_at=t1, labels=["area/backend"], additions=100),
        PullRequest(number=2, title="PR 2", author="bob", created_at=t1, labels=["area/frontend"], additions=200),
        PullRequest(number=3, title="PR 3", author="charlie", created_at=t1, labels=["area/backend", "urgent"], additions=300)
    ]
    
    service = MetricsService()
    results = service.calculate_label_metrics(prs)
    
    # Labels: area/backend, area/frontend, urgent
    assert len(results) == 3
    
    labels = {r.label: r for r in results}
    
    assert labels["Label: area/backend"].total_prs == 2
    assert labels["Label: area/backend"].metrics["pr_size"].average == 200.0
    
    assert labels["Label: area/frontend"].total_prs == 1
    assert labels["Label: area/frontend"].metrics["pr_size"].average == 200.0
    
    assert labels["Label: urgent"].total_prs == 1
    assert labels["Label: urgent"].metrics["pr_size"].average == 300.0
