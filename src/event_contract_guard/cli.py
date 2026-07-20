import argparse
import json
from pathlib import Path

from event_contract_guard.compatibility import check_backward_compatible
from event_contract_guard.contracts import ContractStore
from event_contract_guard.validation import validate_event


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate events and schema changes")
    parser.add_argument("subject")
    parser.add_argument("document", type=Path)
    parser.add_argument("--contracts", type=Path, default=Path("contracts"))
    parser.add_argument("--schema", action="store_true", help="check a candidate JSON Schema")
    args = parser.parse_args()

    contract = ContractStore(args.contracts).load(args.subject)
    candidate = json.loads(args.document.read_text(encoding="utf-8"))
    if args.schema:
        issues = check_backward_compatible(contract.schema, candidate)
        for issue in issues:
            print(f"{issue.path}: {issue.message}")
        raise SystemExit(1 if issues else 0)

    result = validate_event(contract, candidate)
    for error in result.errors:
        print(error)
    raise SystemExit(0 if result.accepted else 1)


if __name__ == "__main__":
    main()
