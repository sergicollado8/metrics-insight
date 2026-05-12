from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class WorkflowRun:
    """Represents a GitHub Action workflow run."""
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[timedelta]
    html_url: str

    @property
    def duration_seconds(self) -> float:
        """Returns the duration in seconds."""
        if self.duration:
            return self.duration.total_seconds()
        return 0.0
