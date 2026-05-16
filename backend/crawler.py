from urllib.parse import urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import httpx
import feedparser

from settings import settings


def _check_blacklist(url: str) -> None:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if domain in settings.blacklisted_domains:
        raise ValueError(f"Domain blocked: {domain}")


async def fetch_html(url: str) -> str:
    _check_blacklist(url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        html = await page.content()
        await browser.close()
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)[:12000]


async def fetch_rss(feed_url: str) -> list[dict]:
    _check_blacklist(feed_url)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(feed_url, follow_redirects=True)
        resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    return [
        {"title": e.get("title", ""), "url": e.get("link", ""), "summary": e.get("summary", "")}
        for e in feed.entries[:10]
    ]


async def search_and_fetch(keyword: str, site: str | None = None) -> list[str]:
    query = f"site:{site} {keyword}" if site else keyword
    search_url = f"https://www.google.com/search?q={query}&num=5"
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(search_url, timeout=30000)
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href).filter(h => h.startsWith('http') && !h.includes('google'))",
        )
        await browser.close()
    return [l for l in links[:10] if not _is_blacklisted(l)][:5]


def _is_blacklisted(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        return domain in settings.blacklisted_domains
    except Exception:
        return False
