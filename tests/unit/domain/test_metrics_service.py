from datetime import datetime, timezone
from metrics_insight.domain.pull_request import PullRequest
from metrics_insight.domain.metrics_service import MetricsService


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


def test_calculate_metrics_with_unmerged_prs():
    """Verify that unmerged PRs are counted but don't affect lifetime metrics."""
    t1 = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)  # 1h later
    
    prs = [
        # Merged PR
        PullRequest(
            number=1, title="Merged PR", author="alice", 
            created_at=t1, merged_at=t2, closed_at=t2, additions=100
        ),
        # Closed but not merged PR
        PullRequest(
            number=2, title="Closed PR", author="bob", 
            created_at=t1, closed_at=t2, additions=200
        )
    ]
    
    service = MetricsService()
    result = service.calculate_team_metrics(prs)
    
    assert result.total_prs == 2
    assert result.merged_prs == 1
    assert result.closed_unmerged_prs == 1
    
    # lifetime_h should only be calculated for the merged one
    # 1h duration
    assert result.metrics["pr_lifetime_h"].average == 1.0
