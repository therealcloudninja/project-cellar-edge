"""Cloud ingest service — receives batches from edge-collector instances.

This is the 'headquarters' side of the architecture: it doesn't
make safety decisions (that's the edge's job), it validates,
deduplicates, and persists what every site reports in.
"""

from fastapi import FastAPI

from cloud_aggregator.models import IngestBatch

app = FastAPI(title="cloud-aggregator")

# In-memory store for now — Day 5 scope is "prove the pipe works
# end to end." Real persistence (Azure Blob Storage) comes later,
# once the Azure infrastructure itself exists.
_received_readings: list[dict] = []


@app.get("/healthz")
def healthz():
    """Liveness: is the process itself running at all?

    Kubernetes uses this to decide whether to restart the
    container. It should only ever fail if the app is truly
    broken, not just busy or temporarily degraded.
    """
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    """Readiness: is this instance currently able to serve traffic?

    Different question from liveness. An instance can be alive
    but not ready — e.g. still starting up. For now this always
    returns ready, but this is the hook where a real deployment
    would check things like 'is the database connection up.'
    """
    return {"status": "ready"}


@app.post("/ingest")
def ingest(batch: IngestBatch):
    """Receive a batch of readings from an edge-collector instance."""
    for reading in batch.readings:
        _received_readings.append(reading.model_dump())

    return {"accepted": len(batch.readings)}


@app.get("/metrics")
def metrics():
    """Minimal placeholder — real Prometheus-format metrics come later."""
    return {"total_readings_received": len(_received_readings)}
