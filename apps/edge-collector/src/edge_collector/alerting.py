"""Local threshold alerting.

This is the module that makes the 'no internet dependency'
promise real: it evaluates a reading and decides whether to
alarm entirely on-device, with zero network calls involved.
"""

import json
import logging
import sys
import uuid
from datetime import datetime, timezone

from edge_collector.sensors import SensorReading

logger = logging.getLogger("edge_collector")


def configure_logging():
    """Structured JSON logging with a correlation ID per run.

    Plain text logs are fine for a human watching a terminal,
    but they're painful to search or aggregate later. JSON lines
    are what a real log pipeline (Azure Monitor, in this project)
    expects to ingest.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_fields"):
            payload.update(record.extra_fields)
        return json.dumps(payload)


class AlarmEngine:
    """Evaluates readings against safe range, locally, instantly."""

    def __init__(self, run_id: str | None = None):
        self.run_id = run_id or str(uuid.uuid4())
        self._currently_alarming = False

    def evaluate(self, reading: SensorReading) -> bool:
        """Returns True if this reading is in an alarm state."""
        safe = reading.is_within_safe_range()

        if not safe and not self._currently_alarming:
            self._currently_alarming = True
            logger.warning(
                "ALARM: reading outside safe range",
                extra={
                    "extra_fields": {
                        "run_id": self.run_id,
                        "device_id": reading.device_id,
                        "temperature_c": round(reading.temperature_c, 2),
                        "humidity_pct": round(reading.humidity_pct, 2),
                        "event": "alarm_start",
                    }
                },
            )
        elif safe and self._currently_alarming:
            self._currently_alarming = False
            logger.info(
                "Reading back within safe range",
                extra={
                    "extra_fields": {
                        "run_id": self.run_id,
                        "device_id": reading.device_id,
                        "event": "alarm_cleared",
                    }
                },
            )

        return not safe
