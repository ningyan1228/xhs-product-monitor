from __future__ import annotations

import logging
import sys

from config import load_settings
from exporter import export_json
from storage import dedupe_latest, load_records, save_records, sort_records


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def read_notes(path, limit: int) -> list[str]:
    if not path.exists():
        logging.warning("notes 文件不存在：%s", path)
        return []
    urls = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
        if len(urls) >= limit:
            break
    return urls


def main() -> int:
    setup_logging()
    settings = load_settings()
    note_urls = read_notes(settings.notes_file, settings.max_notes_per_run)
    if not note_urls:
        logging.info("没有可采集的笔记链接，请先填写 notes.txt。")
        existing = sort_records(dedupe_latest(load_records(settings.csv_path)))
        save_records(settings.csv_path, existing)
        export_json(settings.json_path, existing)
        return 0

    from crawler import StopCrawlingError, crawl_notes

    try:
        new_records = crawl_notes(
            note_urls=note_urls,
            user_data_dir=str(settings.user_data_dir),
            headless=settings.headless,
            wait_seconds=settings.wait_seconds,
        )
    except StopCrawlingError as exc:
        logging.error(str(exc))
        return 2
    except Exception:
        logging.exception("采集任务异常中止。")
        return 1

    existing = load_records(settings.csv_path)
    merged = sort_records(dedupe_latest([*existing, *new_records]))
    save_records(settings.csv_path, merged)
    export_json(settings.json_path, merged)
    logging.info("完成：新增采集 %s 条，当前保留 %s 条去重记录。", len(new_records), len(merged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
