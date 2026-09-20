"""
Local persistent buffer for sensor readings that failed to send to the cloud.

Uses SQLite (built into Python's standard library — no extra dependency)
so that buffered readings survive even if the edge-collector process itself
restarts while the network is still down.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from edge_collector.sensors import SensorReading

DEFAULT_DB_PATH = Path("edge_buffer.db")


@dataclass
class BufferedReading:
    """A SensorReading plus the row id it's stored under, so we can delete it later."""
    row_id: int
    reading: SensorReading


class ReadingBuffer:
    """Persists SensorReadings that couldn't be sent, so they can be replayed later."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS buffered_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    temperature_c REAL NOT NULL,
                    humidity_pct REAL NOT NULL
                )
                """
            )

    def add(self, reading: SensorReading) -> None:
        """Store a reading that failed to send."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO buffered_readings
                    (device_id, timestamp, temperature_c, humidity_pct)
                VALUES (?, ?, ?, ?)
                """,
                (
                    reading.device_id,
                    reading.timestamp.isoformat(),
                    reading.temperature_c,
                    reading.humidity_pct,
                ),
            )

    def get_all(self) -> list[BufferedReading]:
        """Return every buffered reading, oldest first."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, device_id, timestamp, temperature_c, humidity_pct "
                "FROM buffered_readings ORDER BY id ASC"
            )
            rows = cursor.fetchall()

        return [
            BufferedReading(
                row_id=row[0],
                reading=SensorReading(
                    device_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    temperature_c=row[3],
                    humidity_pct=row[4],
                ),
            )
            for row in rows
        ]

    def delete(self, row_id: int) -> None:
        """Remove a single buffered reading once it's been successfully replayed."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM buffered_readings WHERE id = ?", (row_id,))

    def count(self) -> int:
        """How many readings are currently waiting to be replayed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM buffered_readings")
            return cursor.fetchone()[0]
