from datetime import datetime, timedelta, time, timezone


class BusinessHoursCalculator:
    """Calculates time difference in business hours (08:00-20:00, Mon-Fri)."""

    START_HOUR = 8
    END_HOUR = 20

    @classmethod
    def calculate_duration_h(cls, start: datetime, end: datetime) -> float:
        """
        Calculates the duration in business hours between start and end.
        Both dates must be in UTC.
        """
        if start >= end:
            return 0.0

        total_seconds = 0.0
        current = start

        while current < end:
            if current.weekday() >= 5:
                days_to_add = (7 - current.weekday())
                current = datetime.combine(
                    (current + timedelta(days=days_to_add)).date(),
                    time(cls.START_HOUR, 0)
                ).replace(tzinfo=timezone.utc)
                continue

            if current.hour < cls.START_HOUR:
                current = current.replace(hour=cls.START_HOUR, minute=0, second=0, microsecond=0)
                continue

            if current.hour >= cls.END_HOUR:
                current = datetime.combine(
                    (current + timedelta(days=1)).date(),
                    time(cls.START_HOUR, 0)
                ).replace(tzinfo=timezone.utc)
                continue

            end_of_day = current.replace(hour=cls.END_HOUR, minute=0, second=0, microsecond=0)
            
            segment_end = min(end, end_of_day)
            
            delta = segment_end - current
            total_seconds += delta.total_seconds()
            
            current = segment_end
            if current == end_of_day:
                current = datetime.combine(
                    (current + timedelta(days=1)).date(),
                    time(cls.START_HOUR, 0)
                ).replace(tzinfo=timezone.utc)

        return total_seconds / 3600.0
