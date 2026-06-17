from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


PRICE_RE = re.compile(r"(?:¥|￥)\s*([0-9]+(?:\.[0-9]+)?)")
SOLD_RE = re.compile(r"已\s*售\s*([0-9,.]+)\s*([万wW]?)")
AUTHOR_PATTERNS = [
    re.compile(r"作者[:：]\s*([^\n\r]{1,40})"),
    re.compile(r"昵称[:：]\s*([^\n\r]{1,40})"),
]


@dataclass(frozen=True)
class ParsedProduct:
    product_name: str
    price: float | None
    sold_count: int | None


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_price(text: str) -> float | None:
    match = PRICE_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_sold_count(text: str) -> int | None:
    match = SOLD_RE.search(text)
    if not match:
        return None
    raw_number = match.group(1).replace(",", "")
    unit = match.group(2).lower()
    try:
        number = float(raw_number)
    except ValueError:
        return None
    if unit in {"万", "w"}:
        number *= 10000
    return int(number)


def parse_product_name(text: str) -> str | None:
    lines = [normalize_space(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return None

    joined = normalize_space(text)
    label_match = re.search(
        r"(?:商品名|商品名称|名称)[:：]\s*(.+?)(?=(?:¥|￥|价格|已\s*售|销量|$))",
        joined,
    )
    if label_match:
        name = normalize_space(label_match.group(1))
        if name:
            return name

    for line in lines:
        if PRICE_RE.search(line) or SOLD_RE.search(line):
            continue
        if line in {"购买", "去购买", "商品", "店铺"}:
            continue
        if len(line) <= 80:
            return line
    return None


def parse_product_text(text: str) -> ParsedProduct | None:
    name = parse_product_name(text)
    price = parse_price(text)
    sold_count = parse_sold_count(text)
    if not name or price is None and sold_count is None:
        return None
    return ParsedProduct(product_name=name, price=price, sold_count=sold_count)


def parse_products_from_text_blocks(text_blocks: Iterable[str]) -> list[ParsedProduct]:
    products: list[ParsedProduct] = []
    seen: set[tuple[str, float | None, int | None]] = set()
    for text in text_blocks:
        parsed = parse_product_text(text)
        if not parsed:
            continue
        key = (parsed.product_name, parsed.price, parsed.sold_count)
        if key in seen:
            continue
        seen.add(key)
        products.append(parsed)
    return products


def parse_author_name(page_text: str) -> str:
    for pattern in AUTHOR_PATTERNS:
        match = pattern.search(page_text)
        if match:
            return normalize_space(match.group(1))
    lines = [normalize_space(line) for line in page_text.splitlines()]
    for line in lines[:12]:
        if line and len(line) <= 40 and not PRICE_RE.search(line) and not SOLD_RE.search(line):
            return line
    return ""
