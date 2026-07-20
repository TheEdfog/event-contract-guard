from pathlib import Path

from fastapi.testclient import TestClient

from event_contract_guard.api import create_app

CONTRACTS = Path(__file__).parents[1] / "contracts"


def test_valid_event_is_accepted() -> None:
    client = TestClient(create_app(CONTRACTS))
    response = client.post(
        "/validate/retail.orders.v1",
        json={
            "event_id": "238e8192-b02d-4a9e-b210-657067621bbc",
            "event_time": "2026-07-20T10:30:00Z",
            "order_id": "d889ffd9-ac5a-45ea-a10f-bbd17e05f30a",
            "store_id": 4,
            "amount": 1499.0,
            "currency": "RUB",
            "status": "paid",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"accepted": True, "contract_version": 1}


def test_invalid_event_returns_quarantine_envelope() -> None:
    client = TestClient(create_app(CONTRACTS))
    response = client.post(
        "/validate/retail.orders.v1",
        json={"event_id": "bad", "amount": -1, "currency": "rub"},
    )
    body = response.json()
    assert body["accepted"] is False
    assert body["quarantine"]["reason"] == "contract_validation_failed"
    assert len(body["quarantine"]["errors"]) >= 3


def test_invalid_uuid_and_timestamp_formats_are_rejected() -> None:
    client = TestClient(create_app(CONTRACTS))
    response = client.post(
        "/validate/retail.orders.v1",
        json={
            "event_id": "not-a-uuid",
            "event_time": "yesterday",
            "order_id": "also-not-a-uuid",
            "store_id": 1,
            "amount": 10,
            "currency": "RUB",
            "status": "paid",
        },
    )
    errors = response.json()["quarantine"]["errors"]
    assert any("uuid" in error for error in errors)
    assert any("date-time" in error for error in errors)


def test_incompatible_candidate_is_explained() -> None:
    client = TestClient(create_app(CONTRACTS))
    schema = {
        "type": "object",
        "required": ["event_id", "region"],
        "properties": {
            "event_id": {"type": "string"},
            "region": {"type": "string"},
        },
    }
    response = client.post("/compatibility/retail.orders.v1", json={"schema": schema})
    assert response.status_code == 200
    assert response.json()["compatible"] is False
