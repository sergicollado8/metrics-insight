from datetime import datetime, timezone
from metrics_insight.domain.business_hours import BusinessHoursCalculator


def test_calculate_duration_same_day():
    """Verify calculation within the same business day."""
    start = datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc)  # Thursday
    end = datetime(2026, 4, 2, 11, 30, tzinfo=timezone.utc)
    # 2.5 hours
    assert BusinessHoursCalculator.calculate_duration_h(start, end) == 2.5


def test_calculate_duration_over_night():
    """Verify calculation across one night."""
    start = datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc)  # Thursday
    end = datetime(2026, 4, 3, 10, 0, tzinfo=timezone.utc)   # Friday
    # Thu 18:00 to 20:00 (2h) + Fri 08:00 to 10:00 (2h) = 4h
    assert BusinessHoursCalculator.calculate_duration_h(start, end) == 4.0


def test_calculate_duration_over_weekend():
    """Verify calculation across a weekend."""
    start = datetime(2026, 4, 3, 18, 0, tzinfo=timezone.utc)  # Friday
    end = datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)   # Monday
    # Fri 18:00 to 20:00 (2h) + Mon 08:00 to 10:00 (2h) = 4h
    assert BusinessHoursCalculator.calculate_duration_h(start, end) == 4.0


def test_calculate_duration_outside_hours():
    """Verify calculation when start/end are outside business hours."""
    start = datetime(2026, 4, 2, 4, 0, tzinfo=timezone.utc)   # Thursday early
    end = datetime(2026, 4, 2, 22, 0, tzinfo=timezone.utc)   # Thursday late
    # 08:00 to 20:00 = 12h
    assert BusinessHoursCalculator.calculate_duration_h(start, end) == 12.0
