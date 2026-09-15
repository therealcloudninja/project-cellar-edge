"""Sends batched readings to the cloud aggregator.

Deliberately separate from sensors.py and alerting.py — this
module owns the one part of the system that depends on the
network, and nothing else does. If this module fails entirely,
alerting still works; only the "send it to the cloud" job is
affected.
"""

import logging

import httpx

from edge_collector.sensors import SensorReading

logger = logging.getLogger("edge_collector")

# Keep these short and explicit — a hung request is worse than a
# fast failure, since a fast failure lets the caller move on to
# buffering instead of blocking indefinitely.
CONNECT_TIMEOUT_S = 3.0
READ_TIMEOUT_S = 5.0


class Transmitter:
    """Sends a batch of readings to the cloud aggregator over HTTP."""

    def __init__(self, aggregator_url: str):
        self.aggregator_url = aggregator_url.rstrip("/")
        self._client = httpx.Client(
            timeout=httpx.Timeout(
                connect=CONNECT_TIMEOUT_S,
                read=READ_TIMEOUT_S,
                write=READ_TIMEOUT_S,
                pool=READ_TIMEOUT_S,
            )
        )

    def send_batch(self, readings: list[SensorReading]) -> bool:
        """Attempts to send a batch. Returns True on success, False on any failure.

        Deliberately returns a bool rather than raising — the caller
        (main collector loop) needs to decide what to do on failure
        (buffer it), not have an exception propagate and crash the
        whole process over a single failed network call.
        """
        if not readings:
            return True

        payload = {"readings": [r.to_dict() for r in readings]}

        try:
            response = self._client.post(
                f"{self.aggregator_url}/ingest",
                json=payload,
            )
            response.raise_for_status()
            logger.info(
                "Sent batch to aggregator",
                extra={
                    "extra_fields": {
                        "event": "batch_sent",
                        "count": len(readings),
                    }
                },
            )
            return True

        except httpx.TimeoutException:
            logger.warning(
                "Send timed out",
                extra={"extra_fields": {"event": "send_timeout", "count": len(readings)}},
            )
            return False

        except httpx.HTTPStatusError as e:
            logger.warning(
                "Aggregator rejected batch",
                extra={
                    "extra_fields": {
                        "event": "send_rejected",
                        "status_code": e.response.status_code,
                        "count": len(readings),
                    }
                },
            )
            return False

        except httpx.RequestError:
            logger.warning(
                "Could not reach aggregator",
                extra={"extra_fields": {"event": "send_unreachable", "count": len(readings)}},
            )
            return False

    def close(self):
        self._client.close()
