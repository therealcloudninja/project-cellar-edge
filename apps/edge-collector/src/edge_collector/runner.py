"""The orchestration loop that ties edge-collector's modules together.

sensors.py, alerting.py, transmitter.py, and buffer.py each know how
to do one job and nothing about looping or each other. This module
is the one piece that knows the sequence and the timing — read a
reading, evaluate it, try to send it — forever, until stopped.
"""

import logging
import os
import time

from edge_collector.alerting import AlarmEngine, configure_logging
from edge_collector.buffer import ReadingBuffer
from edge_collector.sensors import SensorSimulator
from edge_collector.transmitter import Transmitter

logger = logging.getLogger("edge_collector")

READING_INTERVAL_S = 30

AGGREGATOR_URL = os.getenv("AGGREGATOR_URL", "http://127.0.0.1:8000")


def run() -> None:
    """Runs the read → evaluate → send/buffer cycle forever."""
    configure_logging()

    simulator = SensorSimulator(device_id="cellar-01")
    alarm_engine = AlarmEngine()
    buffer = ReadingBuffer()
    transmitter = Transmitter(aggregator_url=AGGREGATOR_URL, buffer=buffer)

    logger.info(
        "edge-collector starting",
        extra={
            "extra_fields": {
                "event": "collector_started",
                "aggregator_url": AGGREGATOR_URL,
                "interval_s": READING_INTERVAL_S,
            }
        },
    )

    try:
        while True:
            reading = simulator.read()
            alarm_engine.evaluate(reading)
            transmitter.send_batch([reading])
            time.sleep(READING_INTERVAL_S)
    except KeyboardInterrupt:
        logger.info(
            "edge-collector stopping",
            extra={"extra_fields": {"event": "collector_stopped"}},
        )
    finally:
        transmitter.close()


if __name__ == "__main__":
    run()
