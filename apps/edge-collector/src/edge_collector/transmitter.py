"""Sends batched readings to the cloud aggregator.

Deliberately separate from sensors.py and alerting.py — this
module owns the one part of the system that depends on the
network, and nothing else does. If this module fails entirely,
alerting still works; only the "send it to the cloud" job is
affected.

It also owns retry-through-buffering: if a send fails, the reading
is handed to a ReadingBuffer (buffer.py) for local persistence
rather than being lost. ReadingBuffer itself has no network code —
it's a local-storage collaborator this module calls into when the
network isn't cooperating, not a second network dependency.
"""

import logging

import httpx

from edge_collector.buffer import ReadingBuffer
from edge_collector.sensors import SensorReading

logger = logging.getLogger("edge_collector")

# Keep these short and explicit — a hung request is worse than a
# fast failure, since a fast failure lets the caller move on to
# buffering instead of blocking indefinitely.
CONNECT_TIMEOUT_S = 3.0
READ_TIMEOUT_S = 5.0


class Transmitter:
    """Sends a batch of readings to the cloud aggregator over HTTP.

    If a ReadingBuffer is supplied, any reading that fails to send
    is persisted locally, and every future call first tries to
    flush anything already waiting in the buffer — oldest first —
    before sending the new batch, so order is preserved.
    """

    def __init__(self, aggregator_url: str, buffer: ReadingBuffer | None = None, transport: httpx.BaseTransport | None = None):
        self.aggregator_url = aggregator_url.rstrip("/")
        self._buffer = buffer
        self._client = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(
                connect=CONNECT_TIMEOUT_S,
                read=READ_TIMEOUT_S,
                write=READ_TIMEOUT_S,
                pool=READ_TIMEOUT_S,
            ),
        )

    def send_batch(self, readings: list[SensorReading]) -> bool:
        """Attempts to send a batch, flushing any buffered backlog first.

        Deliberately returns a bool rather than raising — the caller
        (main collector loop) needs to decide what to do on failure,
        not have an exception propagate and crash the whole process
        over a single failed network call.
        """
        if not readings:
            return True

        if self._buffer is not None and not self._flush_buffer():
            # The backlog still won't send — don't even attempt the
            # new readings out of order ahead of it. Buffer them too
            # and stop; we'll try everything again next cycle.
            for reading in readings:
                self._buffer.add(reading)
            return False

        success = self._send_http(readings)

        if not success and self._buffer is not None:
            for reading in readings:
                self._buffer.add(reading)

        return success

    def _flush_buffer(self) -> bool:
        """Tries to resend everything currently buffered, oldest first.

        Only deletes buffered rows once the aggregator has actually
        confirmed receipt — a failed send leaves the buffer untouched
        so nothing is ever lost between "sent" and "deleted."
        """
        buffered = self._buffer.get_all()
        if not buffered:
            return True

        readings = [b.reading for b in buffered]
        if not self._send_http(readings):
            return False

        for b in buffered:
            self._buffer.delete(b.row_id)

        logger.info(
            "Flushed buffered readings",
            extra={"extra_fields": {"event": "buffer_flushed", "count": len(buffered)}},
        )
        return True

    def _send_http(self, readings: list[SensorReading]) -> bool:
        """The actual HTTP call — used for both new readings and buffer flushes."""
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
