from edge_collector.sensors import SensorReading
from datetime import datetime, timezone


def test_reading_within_safe_range():
    reading = SensorReading(
        device_id="test",
        timestamp=datetime.now(timezone.utc),
        temperature_c=13.0,
        humidity_pct=60.0,
    )
    assert reading.is_within_safe_range() is True


def test_reading_outside_safe_range():
    reading = SensorReading(
        device_id="test",
        timestamp=datetime.now(timezone.utc),
        temperature_c=16.0,
        humidity_pct=60.0,
    )
    assert reading.is_within_safe_range() is False
