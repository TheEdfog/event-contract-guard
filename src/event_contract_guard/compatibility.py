from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompatibilityIssue:
    path: str
    message: str


def check_backward_compatible(
    current: dict[str, Any], candidate: dict[str, Any]
) -> list[CompatibilityIssue]:
    """Check whether existing producer payloads remain valid under a candidate schema."""
    issues: list[CompatibilityIssue] = []
    old_properties = current.get("properties", {})
    new_properties = candidate.get("properties", {})
    old_required = set(current.get("required", []))
    new_required = set(candidate.get("required", []))

    for name in sorted(old_properties.keys() - new_properties.keys()):
        issues.append(CompatibilityIssue(name, "existing field was removed"))

    for name in sorted(new_required - old_required):
        issues.append(CompatibilityIssue(name, "new required field rejects existing events"))

    for name in sorted(old_properties.keys() & new_properties.keys()):
        old_field = old_properties[name]
        new_field = new_properties[name]
        if old_field.get("type") != new_field.get("type"):
            issues.append(
                CompatibilityIssue(
                    name,
                    f"type changed from {old_field.get('type')} to {new_field.get('type')}",
                )
            )
        old_enum = set(old_field.get("enum", []))
        new_enum = set(new_field.get("enum", []))
        if old_enum and new_enum and not old_enum.issubset(new_enum):
            issues.append(CompatibilityIssue(name, "enum values were removed"))

    return issues
