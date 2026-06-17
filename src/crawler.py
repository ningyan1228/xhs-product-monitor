from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from parser import parse_author_name, parse_products_from_text_blocks
from storage import ProductRecord


LOGGER = logging.getLogger(__name__)

CAPTCHA_WORDS = ["验证码", "安全验证", "滑块", "验证一下", "异常访问"]
LOGIN_WORDS = ["登录后查看", "登录小红书", "请登录"]
PRODUCT_HINT_SELECTORS = [
    "text=已售",
    "text=¥",
    "text=￥",
    "[class*=product]",
    "[class*=goods]",
    "[class*=商品]",
]


class StopCrawlingError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _contains_any(text: str, words: Iterable[str]) -> bool:
    return any(word in text for word in words)


def _text_blocks(page: Page) -> list[str]:
    blocks = page.locator("body *").evaluate_all(
        """nodes => nodes
            .map(node => (node.innerText || '').trim())
            .filter(text => text && text.includes('已售') && /[¥￥]/.test(text))
        """
    )
    if isinstance(blocks, list):
        return [str(item) for item in blocks]
    return []


def _wait_for_product_hint(page: Page, wait_seconds: int) -> None:
    timeout = max(wait_seconds, 1) * 1000
    for selector in PRODUCT_HINT_SELECTORS:
        try:
            page.locator(selector).first.wait_for(state="visible", timeout=timeout)
            return
        except PlaywrightTimeoutError:
            continue


def crawl_note_page(context: BrowserContext, url: str, wait_seconds: int) -> list[ProductRecord]:
    page = context.new_page()
    try:
        LOGGER.info("打开笔记：%s", url)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        _wait_for_product_hint(page, wait_seconds)

        page_text = page.locator("body").inner_text(timeout=5000)
        if _contains_any(page_text, CAPTCHA_WORDS):
            raise StopCrawlingError("页面出现验证码或安全验证，请在有头浏览器中手动处理后再运行。")
        if _contains_any(page_text, LOGIN_WORDS):
            raise StopCrawlingError("登录状态可能失效，请使用 HEADLESS=false 手动登录后再运行。")

        blocks = _text_blocks(page)
        products = parse_products_from_text_blocks(blocks)
        if not products:
            LOGGER.warning("未发现商品卡片，跳过：%s", url)
            return []

        author_name = parse_author_name(page_text)
        captured_at = _utc_now()
        records = [
            ProductRecord(
                product_name=item.product_name,
                price=item.price,
                sold_count=item.sold_count,
                note_url=url,
                author_name=author_name,
                captured_at=captured_at,
                source_type="note",
            )
            for item in products
        ]
        LOGGER.info("采集到 %s 个商品卡片：%s", len(records), url)
        return records
    except PlaywrightTimeoutError as exc:
        LOGGER.error("页面加载或等待超时：%s", url)
        raise RuntimeError(f"页面加载或等待超时：{url}") from exc
    finally:
        page.close()


def crawl_notes(note_urls: list[str], user_data_dir: str, headless: bool, wait_seconds: int) -> list[ProductRecord]:
    results: list[ProductRecord] = []
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            viewport={"width": 1366, "height": 900},
            locale="zh-CN",
        )
        try:
            for url in note_urls:
                records = crawl_note_page(context, url, wait_seconds)
                results.extend(records)
        finally:
            context.close()
    return results
