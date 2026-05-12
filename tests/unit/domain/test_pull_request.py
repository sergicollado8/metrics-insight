from datetime import datetime, timezone
from src.metrics_insight.domain.pull_request import PullRequest, Review


def test_pull_request_size():
    """Verify that PR size is calculated correctly."""
    pr = PullRequest(
        number=1,
        title="Test PR",
        author="user1",
        created_at=datetime.now(timezone.utc),
        additions=10,
        deletions=5
    )
    assert pr.size == 15


def test_first_human_review():
    """Verify that the first human review (excluding author) is identified correctly."""
    t1 = datetime(2026, 4, 2, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 4, 2, 11, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 4, 2, 12, 0, tzinfo=timezone.utc)

    reviews = [
        Review(submitted_at=t1, author="user1", is_bot=False), # Author review - should be skipped
        Review(submitted_at=t2, author="human1", is_bot=False),
        Review(submitted_at=t3, author="human2", is_bot=False),
    ]

    pr = PullRequest(
        number=1,
        title="Test PR",
        author="user1",
        created_at=datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc),
        reviews=reviews
    )

    first_review = pr.first_human_review
    assert first_review is not None
    assert first_review.author == "human1"
    assert first_review.submitted_at == t2


def test_waiting_for_author_h():
    """Verify that waiting_for_author_h uses first_rework_at if available."""
    # Business hours are 08:00 to 20:00, Mon-Fri
    t_review = datetime(2026, 4, 2, 10, 0, tzinfo=timezone.utc) # Thursday
    t_rework = datetime(2026, 4, 2, 14, 0, tzinfo=timezone.utc) # Thursday (+4h)
    
    pr = PullRequest(
        number=1,
        title="Test PR",
        author="user1",
        created_at=datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc),
        reviews=[Review(submitted_at=t_review, author="reviewer1", is_bot=False)],
        first_rework_at=t_rework
    )
    
    # 14:00 - 10:00 = 4 hours
    assert pr.waiting_for_author_h == 4.0


def test_waiting_for_author_h_fallback_to_merge():
    """Verify that waiting_for_author_h falls back to merged_at if no first_rework_at."""
    t_review = datetime(2026, 4, 2, 10, 0, tzinfo=timezone.utc) # Thursday
    t_merge = datetime(2026, 4, 2, 16, 0, tzinfo=timezone.utc) # Thursday (+6h)
    
    pr = PullRequest(
        number=1,
        title="Test PR",
        author="user1",
        created_at=datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc),
        reviews=[Review(submitted_at=t_review, author="reviewer1", is_bot=False)],
        merged_at=t_merge
    )
    
    # 16:00 - 10:00 = 6 hours
    assert pr.waiting_for_author_h == 6.0


def test_pull_request_labels():
    """Verify that labels are correctly stored."""
    pr = PullRequest(
        number=1,
        title="Test PR",
        author="user1",
        created_at=datetime.now(timezone.utc),
        labels=["area/frontend", "type/feature"]
    )
    assert "area/frontend" in pr.labels
    assert "type/feature" in pr.labels
    assert len(pr.labels) == 2
