from datetime import datetime

from edge_collector.buffer import ReadingBuffer
from edge_collector.sensors import SensorReading


def make_reading(temp=13.0):
    return SensorReading(
        device_id="cellar-01",
        timestamp=datetime(2026, 9, 20, 18, 0, 0),
        temperature_c=temp,
        humidity_pct=60.0,
    )


def test_add_and_get_all(tmp_path):
    buf = ReadingBuffer(db_path=tmp_path / "test.db")
    buf.add(make_reading(13.0))
    buf.add(make_reading(14.0))

    all_readings = buf.get_all()
    assert len(all_readings) == 2
    assert all_readings[0].reading.temperature_c == 13.0
    assert all_readings[1].reading.temperature_c == 14.0


def test_delete_removes_only_that_row(tmp_path):
    buf = ReadingBuffer(db_path=tmp_path / "test.db")
    buf.add(make_reading(13.0))
    buf.add(make_reading(14.0))

    first_row_id = buf.get_all()[0].row_id
    buf.delete(first_row_id)

    remaining = buf.get_all()
    assert len(remaining) == 1
    assert remaining[0].reading.temperature_c == 14.0


def test_count_matches_number_of_rows(tmp_path):
    buf = ReadingBuffer(db_path=tmp_path / "test.db")
    assert buf.count() == 0

    buf.add(make_reading())
    assert buf.count() == 1
