from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from metrics_insight.application.compare_sprints import CompareSprints
from metrics_insight.domain.pull_request import PullRequest


def test_compare_sprints_logic():
    """Verify that CompareSprints correctly iterates and aggregates across multiple sprints."""
    # Mock ports
    repo_mock = MagicMock()
    exporter_mock = MagicMock()
    
    # Setup test data: 2 sprints, 1 PR each
    t_start = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    pr1 = PullRequest(number=1, title="PR 1", author="alice", created_at=t_start)
    pr2 = PullRequest(number=2, title="PR 2", author="bob", created_at=t_start + timedelta(weeks=2))
    
    # Mock get_pull_requests to return PRs based on current window
    def side_effect(repo, start, end):
        if pr1.created_at >= start and pr1.created_at < end:
            return [pr1]
        elif pr2.created_at >= start and pr2.created_at < end:
            return [pr2]
        return []
        
    repo_mock.get_pull_requests.side_effect = side_effect
    
    # Run use case: 2 weeks per sprint, 2 sprints
    use_case = CompareSprints(repo_mock, exporter_mock)
    results = use_case.execute("owner/repo", t_start, 2, 2, "/tmp/output")
    
    # Assertions
    assert len(results) == 2
    assert results[0]["label"] == "Sprint 1"
    assert results[0]["total_prs"] == 1
    assert results[1]["label"] == "Sprint 2"
    assert results[1]["total_prs"] == 1
    
    # Verify mock was called for each sprint
    assert repo_mock.get_pull_requests.call_count == 2
