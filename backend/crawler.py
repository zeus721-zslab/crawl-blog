import logging
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from settings import settings

log = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; crawl-blog/1.0; +https://github.com)"
    )
}


def _check_blacklist(url: str) -> None:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if domain in settings.blacklisted_domains:
        raise ValueError(f"Domain blocked: {domain}")


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)[:12000]


# ── RSS ────────────────────────────────────────────────────────────────────

async def fetch_rss(feed_url: str) -> list[dict]:
    """Fetch RSS/Atom feed entries. Returns up to 10 items."""
    _check_blacklist(feed_url)
    async with httpx.AsyncClient(timeout=15, headers=_HEADERS) as client:
        resp = await client.get(feed_url, follow_redirects=True)
        resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    return [
        {
            "title": e.get("title", ""),
            "url": e.get("link", ""),
            "summary": e.get("summary", ""),
        }
        for e in feed.entries[:10]
        if e.get("link")
    ]


# ── HTML (simple, no JS) ───────────────────────────────────────────────────

async def _fetch_html_simple(url: str) -> str:
    async with httpx.AsyncClient(timeout=20, headers=_HEADERS, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return _extract_text(resp.text)


# ── HTML (Playwright fallback for JS-heavy pages) ──────────────────────────

async def _fetch_html_playwright(url: str) -> str:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
        finally:
            await browser.close()
    return _extract_text(html)


# ── Public: fetch a page with RSS auto-detect + fallback chain ─────────────

async def fetch_page(url: str, method: str = "html") -> str:
    """
    Fetch page content using the prescribed method.
    Priority: rss > html (simple) > playwright
    Falls back to Playwright when simple HTTP fails.
    """
    _check_blacklist(url)

    if method == "rss":
        entries = await fetch_rss(url)
        if entries:
            # Concatenate summaries of top entries for a single refine pass
            parts = [f"# {e['title']}\n{e['summary']}" for e in entries[:3]]
            return "\n\n---\n\n".join(parts)
        # RSS advertised but no entries → fall through to HTML
        log.warning("RSS returned no entries for %s, falling back to HTML", url)

    # Try simple HTTP first (no Playwright overhead)
    try:
        return await _fetch_html_simple(url)
    except Exception as exc:
        if method == "playwright":
            # Already intended to use Playwright; log and proceed
            log.debug("Simple fetch failed (%s), using Playwright for %s", exc, url)
        else:
            log.info("Simple fetch failed (%s), falling back to Playwright for %s", exc, url)

    return await _fetch_html_playwright(url)
