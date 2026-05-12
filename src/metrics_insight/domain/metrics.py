import statistics
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class AggregatedMetric:
    """Represents a set of statistics for a specific metric."""
    min: float
    average: float
    median: float
    p85: float
    max: float
    count: int


class MetricCalculator:
    """Calculates aggregates (MIN, AVERAGE, MEDIAN, P85, MAX) for a list of values."""

    @staticmethod
    def calculate_aggregates(values: List[float]) -> Optional[AggregatedMetric]:
        """Calculates aggregates from a list of floats."""
        if not values:
            return None

        sorted_values = sorted(values)
        count = len(sorted_values)
        
        p85_index = int(0.85 * (count - 1))
        p85 = sorted_values[p85_index]

        return AggregatedMetric(
            min=float(min(sorted_values)),
            average=float(statistics.mean(sorted_values)),
            median=float(statistics.median(sorted_values)),
            p85=float(p85),
            max=float(max(sorted_values)),
            count=count
        )
