from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable


def ensure_csv(path: Path, headers: Iterable[str]) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)


def append_row(path: Path, headers: Iterable[str], row: Dict[str, object]) -> None:
    ensure_csv(path, headers)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writerow(row)


def json_dumps(data: Dict[str, object]) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def json_loads(body: bytes) -> Dict[str, object]:
    return json.loads(body.decode("utf-8"))

