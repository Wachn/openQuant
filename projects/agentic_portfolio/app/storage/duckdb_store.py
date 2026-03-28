from __future__ import annotations

import json
from pathlib import Path


class DuckDbStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def upsert_bars(self, rows: list[dict[str, object]]) -> dict[str, object]:
        return {"rows": len(rows), "status": "accepted"}

    def upsert_quotes(self, rows: list[dict[str, object]]) -> dict[str, object]:
        return {"rows": len(rows), "status": "accepted"}

    def write_nav_point(self, point: dict[str, object]) -> dict[str, object]:
        payload = json.loads(json.dumps(point))
        return {"status": "accepted", "point": payload}
