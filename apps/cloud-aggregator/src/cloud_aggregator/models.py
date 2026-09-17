"""Pydantic models — the validation gate for anything entering the system.

Nothing reaches the actual ingest logic without first passing
through these definitions. Bad data (wrong types, missing fields,
values out of sane bounds) gets rejected here, automatically,
before any application code has to think about it.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Reading(BaseModel):
    device_id: str = Field(min_length=1)
    timestamp: datetime
    temperature_c: float = Field(ge=-40.0, le=80.0)
    humidity_pct: float = Field(ge=0.0, le=100.0)


class IngestBatch(BaseModel):
    readings: list[Reading]
