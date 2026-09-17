from fastapi.testclient import TestClient

from cloud_aggregator.main import app

client = TestClient(app)


def test_ingest_accepts_valid_reading():
    response = client.post(
        "/ingest",
        json={
            "readings": [
                {
                    "device_id": "test-room",
                    "timestamp": "2026-09-17T09:30:00Z",
                    "temperature_c": 13.0,
                    "humidity_pct": 60.0,
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["accepted"] == 1


def test_ingest_rejects_implausible_temperature():
    response = client.post(
        "/ingest",
        json={
            "readings": [
                {
                    "device_id": "test-room",
                    "timestamp": "2026-09-17T09:30:00Z",
                    "temperature_c": 999.0,
                    "humidity_pct": 60.0,
                }
            ]
        },
    )
    assert response.status_code == 422
