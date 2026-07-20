from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Contract:
    subject: str
    version: int
    owner: str
    schema: dict[str, Any]


class ContractStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def load(self, subject: str) -> Contract:
        path = self.directory / f"{subject}.yaml"
        if not path.is_file():
            raise KeyError(subject)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        return Contract(
            subject=document["subject"],
            version=document["version"],
            owner=document["owner"],
            schema=document["schema"],
        )

    def subjects(self) -> list[str]:
        return sorted(path.stem for path in self.directory.glob("*.yaml"))
