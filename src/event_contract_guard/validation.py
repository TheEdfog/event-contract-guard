from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator

from event_contract_guard.contracts import Contract


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    errors: tuple[str, ...]


def validate_event(contract: Contract, event: dict[str, Any]) -> ValidationResult:
    validator = Draft202012Validator(contract.schema)
    errors = tuple(
        f"{'/'.join(str(part) for part in error.path) or '$'}: {error.message}"
        for error in sorted(validator.iter_errors(event), key=lambda item: list(item.path))
    )
    return ValidationResult(accepted=not errors, errors=errors)


def quarantine_record(
    *, subject: str, payload: dict[str, Any], errors: tuple[str, ...]
) -> dict[str, Any]:
    return {
        "subject": subject,
        "reason": "contract_validation_failed",
        "errors": list(errors),
        "payload": payload,
    }
