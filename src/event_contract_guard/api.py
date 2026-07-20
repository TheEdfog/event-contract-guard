import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel, ConfigDict, Field

from event_contract_guard.compatibility import check_backward_compatible
from event_contract_guard.contracts import ContractStore
from event_contract_guard.validation import quarantine_record, validate_event

VALIDATED = Counter("contract_events_validated_total", "Validated events", ["subject", "result"])


class CompatibilityRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_: dict[str, Any] = Field(alias="schema")


def create_app(contract_directory: Path | None = None) -> FastAPI:
    directory = contract_directory or Path(os.getenv("CONTRACT_DIRECTORY", "contracts"))
    store = ContractStore(directory)
    app = FastAPI(title="Event Contract Guard", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/contracts")
    def contracts() -> dict[str, list[str]]:
        return {"subjects": store.subjects()}

    @app.post("/validate/{subject}")
    def validate(subject: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            contract = store.load(subject)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="unknown contract") from error
        result = validate_event(contract, payload)
        VALIDATED.labels(
            subject=subject, result="accepted" if result.accepted else "rejected"
        ).inc()
        if result.accepted:
            return {"accepted": True, "contract_version": contract.version}
        return {
            "accepted": False,
            "quarantine": quarantine_record(subject=subject, payload=payload, errors=result.errors),
        }

    @app.post("/compatibility/{subject}")
    def compatibility(subject: str, request: CompatibilityRequest) -> dict[str, Any]:
        try:
            current = store.load(subject)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="unknown contract") from error
        issues = check_backward_compatible(current.schema, request.schema_)
        return {
            "compatible": not issues,
            "issues": [{"path": issue.path, "message": issue.message} for issue in issues],
        }

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
