from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


FIELDS = [
    "product_name",
    "price",
    "sold_count",
    "note_url",
    "author_name",
    "captured_at",
    "source_type",
]


@dataclass(frozen=True)
class ProductRecord:
    product_name: str
    price: float | None
    sold_count: int | None
    note_url: str
    author_name: str
    captured_at: str
    source_type: str = "note"


def _parse_price(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def load_records(csv_path: Path) -> list[ProductRecord]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        records = []
        for row in reader:
            product_name = (row.get("product_name") or "").strip()
            note_url = (row.get("note_url") or "").strip()
            if not product_name or not note_url:
                continue
            records.append(
                ProductRecord(
                    product_name=product_name,
                    price=_parse_price(row.get("price")),
                    sold_count=_parse_int(row.get("sold_count")),
                    note_url=note_url,
                    author_name=(row.get("author_name") or "").strip(),
                    captured_at=(row.get("captured_at") or "").strip(),
                    source_type=(row.get("source_type") or "note").strip(),
                )
            )
        return records


def dedupe_latest(records: Iterable[ProductRecord]) -> list[ProductRecord]:
    latest: dict[tuple[str, str], ProductRecord] = {}
    for record in records:
        key = (record.note_url, record.product_name)
        old = latest.get(key)
        if old is None or record.captured_at >= old.captured_at:
            latest[key] = record
    return list(latest.values())


def sort_records(records: Iterable[ProductRecord]) -> list[ProductRecord]:
    return sorted(
        records,
        key=lambda item: (
            item.sold_count if item.sold_count is not None else -1,
            item.captured_at,
        ),
        reverse=True,
    )


def save_records(csv_path: Path, records: Iterable[ProductRecord]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["price"] = "" if record.price is None else record.price
            row["sold_count"] = "" if record.sold_count is None else record.sold_count
            writer.writerow(row)
