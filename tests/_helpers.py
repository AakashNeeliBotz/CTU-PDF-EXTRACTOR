from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]


def ensure_repo_root_on_path() -> None:
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def load_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def find_first_row(rows: List[Dict[str, str]], **criteria: str) -> Dict[str, str]:
    for row in rows:
        if all((row.get(key) or "") == expected for key, expected in criteria.items()):
            return row
    raise AssertionError(f"No row matched criteria: {criteria}")


def find_rows(rows: List[Dict[str, str]], **criteria: str) -> List[Dict[str, str]]:
    matched = []
    for row in rows:
        if all((row.get(key) or "") == expected for key, expected in criteria.items()):
            matched.append(row)
    return matched
