from datetime import datetime, timezone, timedelta
from src.metrics_insight.domain.pull_request import PullRequest, Review
from src.metrics_insight.domain.analyzer import InsightAnalyzer


def test_analyzer_detects_bottleneck():
    """Verify that analyzer identifies slow reviews as bottlenecks."""
    analyzer = InsightAnalyzer()
    
    # PR created at 9:00, reviewed at 11:00 (2h, NOT a bottleneck)
    t_start = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    pr_fast = PullRequest(
        number=1, title="Fast", author="alice", created_at=t_start,
        reviews=[Review(submitted_at=t_start + timedelta(hours=2), author="bob", is_bot=False)]
    )
    
    # PR created at 9:00, reviewed 72h later (Wednesday to Saturday -> Thu(12) + Fri(12) + Mon(08:00) = >24h)
    pr_slow = PullRequest(
        number=2, title="Slow", author="bob", created_at=t_start,
        reviews=[Review(submitted_at=t_start + timedelta(hours=72), author="alice", is_bot=False)]
    )
    
    insights = analyzer.analyze([pr_fast, pr_slow])
    
    # Find bottleneck insight
    bottlenecks = [i for i in insights if i.category == "Bottleneck"]
    assert len(bottlenecks) == 1
    assert "Slow Initial Review" in bottlenecks[0].title
