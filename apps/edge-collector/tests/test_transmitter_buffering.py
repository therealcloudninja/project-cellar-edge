from datetime import datetime

import httpx

from edge_collector.buffer import ReadingBuffer
from edge_collector.sensors import SensorReading
from edge_collector.transmitter import Transmitter


def make_reading(temp=13.0):
    return SensorReading(
        device_id="cellar-01",
        timestamp=datetime(2026, 9, 20, 18, 0, 0),
        temperature_c=temp,
        humidity_pct=60.0,
    )


def failing_handler(request):
    raise httpx.ConnectError("simulated unreachable aggregator", request=request)


def succeeding_handler(request):
    return httpx.Response(200, json={"accepted": 1})


def test_failed_send_buffers_the_reading(tmp_path):
    buf = ReadingBuffer(db_path=tmp_path / "test.db")
    transport = httpx.MockTransport(failing_handler)
    t = Transmitter(aggregator_url="http://fake", buffer=buf, transport=transport)

    result = t.send_batch([make_reading()])

    assert result is False
    assert buf.count() == 1


def test_successful_send_flushes_buffer_first(tmp_path):
    buf = ReadingBuffer(db_path=tmp_path / "test.db")
    buf.add(make_reading(temp=11.0))  # pretend this failed earlier

    transport = httpx.MockTransport(succeeding_handler)
    t = Transmitter(aggregator_url="http://fake", buffer=buf, transport=transport)

    result = t.send_batch([make_reading(temp=12.0)])

    assert result is True
    assert buf.count() == 0  # both the backlog and the new reading went through


def test_new_reading_buffered_if_flush_still_fails(tmp_path):
    buf = ReadingBuffer(db_path=tmp_path / "test.db")
    buf.add(make_reading(temp=11.0))  # existing backlog

    transport = httpx.MockTransport(failing_handler)
    t = Transmitter(aggregator_url="http://fake", buffer=buf, transport=transport)

    result = t.send_batch([make_reading(temp=12.0)])

    assert result is False
    assert buf.count() == 2  # old backlog + new reading, nothing lost, nothing sent out of order
