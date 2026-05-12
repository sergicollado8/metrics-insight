from src.metrics_insight.domain.metrics import MetricCalculator


def test_calculate_aggregates():
    """Verify that all metrics are calculated correctly."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    # count = 10
    # sorted: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
    # min: 10
    # max: 100
    # avg: 55
    # median: 55 (avg of 50 and 60)
    # p85: 0.85 * (10-1) = 0.85 * 9 = 7.65 -> index 7 -> 80

    aggregates = MetricCalculator.calculate_aggregates(values)
    
    assert aggregates is not None
    assert aggregates.min == 10.0
    assert aggregates.max == 100.0
    assert aggregates.average == 55.0
    assert aggregates.median == 55.0
    assert aggregates.p85 == 80.0
    assert aggregates.count == 10


def test_calculate_aggregates_empty():
    """Verify that calculating aggregates for an empty list returns None."""
    assert MetricCalculator.calculate_aggregates([]) is None
