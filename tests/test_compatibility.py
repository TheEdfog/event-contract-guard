from event_contract_guard.compatibility import check_backward_compatible

BASE = {
    "type": "object",
    "required": ["id"],
    "properties": {"id": {"type": "string"}, "status": {"type": "string", "enum": ["new", "paid"]}},
}


def test_optional_field_is_backward_compatible() -> None:
    candidate = {**BASE, "properties": {**BASE["properties"], "note": {"type": "string"}}}
    assert check_backward_compatible(BASE, candidate) == []


def test_new_required_field_is_rejected() -> None:
    candidate = {
        **BASE,
        "required": ["id", "store_id"],
        "properties": {**BASE["properties"], "store_id": {"type": "integer"}},
    }
    issues = check_backward_compatible(BASE, candidate)
    assert [(issue.path, issue.message) for issue in issues] == [
        ("store_id", "new required field rejects existing events")
    ]


def test_json_schema_default_does_not_make_required_field_compatible() -> None:
    candidate = {
        **BASE,
        "required": ["id", "region"],
        "properties": {
            **BASE["properties"],
            "region": {"type": "string", "default": "unknown"},
        },
    }
    assert check_backward_compatible(BASE, candidate)[0].path == "region"


def test_type_change_and_narrower_enum_are_rejected() -> None:
    candidate = {
        **BASE,
        "properties": {
            "id": {"type": "integer"},
            "status": {"type": "string", "enum": ["paid"]},
        },
    }
    messages = {issue.message for issue in check_backward_compatible(BASE, candidate)}
    assert messages == {"type changed from string to integer", "enum values were removed"}
