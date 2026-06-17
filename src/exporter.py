from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from storage import ProductRecord, sort_records


def export_json(json_path: Path, records: Iterable[ProductRecord], limit: int = 1000) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(record) for record in sort_records(records)[:limit]]
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
