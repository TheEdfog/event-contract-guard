from pathlib import Path

from event_contract_guard.contracts import ContractStore
from event_contract_guard.processor import route_event


def test_invalid_event_goes_only_to_quarantine() -> None:
    accepted: list[dict] = []
    quarantined: list[dict] = []
    store = ContractStore(Path(__file__).parents[1] / "contracts")

    result = route_event(
        subject="retail.orders.v1",
        payload={"amount": -10},
        store=store,
        publish_valid=accepted.append,
        publish_quarantine=quarantined.append,
    )

    assert result is False
    assert accepted == []
    assert quarantined[0]["reason"] == "contract_validation_failed"
