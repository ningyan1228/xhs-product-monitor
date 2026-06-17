from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[1]


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _path_env(name: str, default: str) -> Path:
    value = os.getenv(name, default)
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def _load_env_file(path: Path) -> None:
    if load_dotenv is not None:
        load_dotenv(path)
        return
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    headless: bool
    user_data_dir: Path
    notes_file: Path
    csv_path: Path
    json_path: Path
    max_notes_per_run: int
    wait_seconds: int


def load_settings() -> Settings:
    _load_env_file(ROOT_DIR / ".env")
    return Settings(
        headless=_bool_env("HEADLESS", False),
        user_data_dir=_path_env("USER_DATA_DIR", ".browser_profile"),
        notes_file=_path_env("NOTES_FILE", "notes.txt"),
        csv_path=_path_env("CSV_PATH", "data/products.csv"),
        json_path=_path_env("JSON_PATH", "docs/data/products.json"),
        max_notes_per_run=_int_env("MAX_NOTES_PER_RUN", 100),
        wait_seconds=_int_env("WAIT_SECONDS", 5),
    )
