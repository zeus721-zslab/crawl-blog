import logging
import re
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from settings import settings

log = logging.getLogger(__name__)

# Path segments that indicate navigation/taxonomy pages (not articles)
_NAV_SEGMENTS = frozenset({
    "category", "categories", "cat", "tag", "tags", "author", "authors",
    "topic", "topics", "section", "sections", "archive", "archives",
    "event", "events", "podcast", "podcasts", "newsletter", "newsletters",
    "about", "contact", "search", "p", "feed", "rss", "sitemap",
    "wp-content", "wp-admin", "wp-json", "wp-includes",
    "login", "logout", "signup", "register", "account", "profile", "settings",
    "privacy", "terms", "tos", "advertise", "press", "jobs", "careers",
    "photo", "photos", "gallery", "galleries",
    "series", "collection", "collections", "subscribe", "subscription",
})

_DATE_RE = re.compile(r"/20\d{2}/")
_MEDIA_EXT_RE = re.compile(r"\.(jpg|jpeg|png|gif|svg|webp|pdf|zip|mp3|mp4|css|js)$", re.IGNORECASE)


def _is_likely_article(path: str) -> bool:
    """Return True if the URL path looks like a real article rather than a nav/listing page."""
    segments = [s for s in path.split("/") if s]
    if not segments:
        return False
    if _MEDIA_EXT_RE.search(path):
        return False
    # Skip if the first segment is a known nav/taxonomy keyword
    if segments[0].lower() in _NAV_SEGMENTS:
        return False
    # Date pattern in path → very likely an article (e.g. /2025/05/17/slug/)
    if _DATE_RE.search(path):
        return True
    # Two or more segments with a non-nav first segment → section/article structure
    if len(segments) >= 2:
        return True
    # Single-segment paths: accept only if slug is long (suggests article title, not category name)
    return len(segments[0]) > 15


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
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(args=["--no-sandbox"])
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
        finally:
            await browser.close()
    finally:
        await pw.stop()
    return _extract_text(html)


# ── Public: fetch a page with RSS auto-detect + fallback chain ─────────────

def _extract_article_links(html: str, base_url: str) -> list[str]:
    """Extract article-like links from a listing page (same domain, non-root paths)."""
    from urllib.parse import urljoin
    base_parsed = urlparse(base_url)
    base_domain = base_parsed.netloc
    base_path = base_parsed.path.rstrip("/")
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        parsed = urlparse(href)
        if parsed.netloc != base_domain:
            continue
        path = parsed.path.rstrip("/")
        if not path or path == base_path:
            continue
        if not _is_likely_article(path):
            continue
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean in seen:
            continue
        seen.add(clean)
        links.append(clean)
    return links[:10]


async def fetch_links(url: str) -> list[str]:
    """Fetch a listing page via simple HTTP and return extracted article links.
    Returns [] on any error (caller falls back to treating page as single article)."""
    _check_blacklist(url)
    try:
        async with httpx.AsyncClient(timeout=20, headers=_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return _extract_article_links(resp.text, url)
    except Exception as exc:
        log.debug("fetch_links failed for %s: %s", url, exc)
        return []


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
