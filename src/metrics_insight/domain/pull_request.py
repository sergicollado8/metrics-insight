from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass(frozen=True)
class Review:
    """Represents a PR review."""
    submitted_at: datetime
    author: str
    is_bot: bool
    body: Optional[str] = None


@dataclass(frozen=True)
class PullRequest:
    """Domain model for a Pull Request."""
    number: int
    title: str
    author: str
    created_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    additions: int = 0
    deletions: int = 0
    labels: List[str] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    commits_after_first_review: int = 0
    jira_ticket: Optional[str] = None
    
    review_requested_at: Optional[datetime] = None
    last_commit_at: Optional[datetime] = None
    first_rework_at: Optional[datetime] = None
    rework_count: int = 0
    
    author_comments_count: int = 0
    bot_comments_count: int = 0
    other_human_comments_count: int = 0
    
    @property
    def size(self) -> int:
        """Total lines changed."""
        return self.additions + self.deletions

    @property
    def waiting_for_reviewer_h(self) -> float:
        """Time spent waiting for the first review since request."""
        from metrics_insight.domain.business_hours import BusinessHoursCalculator
        start = self.review_requested_at or self.created_at
        first_review = self.first_human_review
        if not first_review:
            return 0.0
        return BusinessHoursCalculator.calculate_duration_h(start, first_review.submitted_at)

    @property
    def waiting_for_author_h(self) -> float:
        """Time spent by the author addressing feedback (Rework)."""
        from metrics_insight.domain.business_hours import BusinessHoursCalculator
        first_review = self.first_human_review
        if not first_review:
            return 0.0
        
        end_time = self.first_rework_at or self.merged_at
        if not end_time:
            return 0.0
            
        return BusinessHoursCalculator.calculate_duration_h(first_review.submitted_at, end_time)

    @property
    def is_merged(self) -> bool:
        """Checks if the PR has been merged.

        Returns:
            bool: True if the PR is merged, False otherwise.
        """
        return self.merged_at is not None

    @property
    def lifetime_h(self) -> float:
        """Calculates total time from creation to merge in business hours.

        Returns:
            float: Duration in business hours, or 0.0 if not merged.
        """
        from metrics_insight.domain.business_hours import BusinessHoursCalculator
        if not self.is_merged:
            return 0.0
        return BusinessHoursCalculator.calculate_duration_h(self.created_at, self.merged_at)

    @property
    def first_human_review(self) -> Optional[Review]:
        """Returns the first review submitted by a human other than the author."""
        human_reviews = [r for r in self.reviews if not r.is_bot and r.author != self.author]
        if not human_reviews:
            return None
        return min(human_reviews, key=lambda r: r.submitted_at)

    @property
    def has_jira_ticket(self) -> bool:
        """Checks if a JIRA ticket is associated."""
        return self.jira_ticket is not None
