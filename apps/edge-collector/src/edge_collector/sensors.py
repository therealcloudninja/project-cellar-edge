"""Simulated sensor readings for a wine storage room.

In a real deployment, this module would read from physical
temperature/humidity sensors (e.g. via GPIO, I2C, or a serial
interface). For this project, readings are simulated with
realistic wine-storage values and occasional drift, so the
downstream alerting and buffering logic can be exercised and
demoed without physical hardware.
"""

import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Safe storage ranges for wine
TEMP_MIN_C = 12.0
TEMP_MAX_C = 14.0
HUMIDITY_MIN_PCT = 50.0
HUMIDITY_MAX_PCT = 70.0

# Baseline values the simulator drifts around during normal operation
BASELINE_TEMP_C = 13.0
BASELINE_HUMIDITY_PCT = 60.0


@dataclass
class SensorReading:
    device_id: str
    timestamp: datetime
    temperature_c: float
    humidity_pct: float

    def is_within_safe_range(self) -> bool:
        return (
            TEMP_MIN_C <= self.temperature_c <= TEMP_MAX_C
            and HUMIDITY_MIN_PCT <= self.humidity_pct <= HUMIDITY_MAX_PCT
        )

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "temperature_c": round(self.temperature_c, 2),
            "humidity_pct": round(self.humidity_pct, 2),
        }


class SensorSimulator:
    """Generates realistic sensor readings with occasional drift.

    Most readings stay close to baseline. A small chance of
    'drift events' lets the simulator demonstrate the alerting
    path without waiting for real equipment to fail.
    """

    def __init__(self, device_id: str, drift_probability: float = 0.02):
        self.device_id = device_id
        self.drift_probability = drift_probability
        self._drifting = False
        self._temp = BASELINE_TEMP_C
        self._humidity = BASELINE_HUMIDITY_PCT

    def _step(self):
        # Small random walk around baseline
        if not self._drifting and random.random() < self.drift_probability:
            self._drifting = True

        if self._drifting:
            # Push temperature/humidity out of safe range gradually
            self._temp += random.uniform(0.1, 0.4)
            self._humidity += random.uniform(-0.5, 0.5)
            # Recover eventually
            if random.random() < 0.1:
                self._drifting = False
        else:
            self._temp += random.uniform(-0.1, 0.1)
            self._humidity += random.uniform(-0.5, 0.5)
            # Gently pull back toward baseline
            self._temp += (BASELINE_TEMP_C - self._temp) * 0.1
            self._humidity += (BASELINE_HUMIDITY_PCT - self._humidity) * 0.1

    def read(self) -> SensorReading:
        self._step()
        return SensorReading(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            temperature_c=self._temp,
            humidity_pct=self._humidity,
        )
