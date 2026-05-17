import logging
from datetime import datetime, timedelta

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import database
import crawler
from llm.factory import get_llm
from settings import settings
import rate

log = logging.getLogger(__name__)

INTERVAL_MAP = {"1h": 1, "6h": 6, "24h": 24}
MAX_REFINE_PER_RUN = 3  # Sonnet refine cap per crawl run

_jobstore_url = (
    f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)
_jobstores = {
    "default": SQLAlchemyJobStore(url=_jobstore_url)
}
_job_defaults = {
    "coalesce": True,       # merge missed runs into one
    "max_instances": 1,     # never run the same job twice concurrently
    "misfire_grace_time": 600,  # tolerate up to 10 min late start
}

scheduler = AsyncIOScheduler(jobstores=_jobstores, job_defaults=_job_defaults)


async def crawl_input(input_id: int) -> None:
    inp = await database.get_input(input_id)
    if not inp or inp["status"] == "deleted":
        return

    await database.update_input(input_id, status="crawling")
    refined_count = 0
    feed_name: str | None = inp.get("name")
    keyword: str | None = inp.get("keyword")

    try:
        method = inp["crawl_method"] or "html"
        url = inp["value"]

        if method == "rss":
            entries = await crawler.fetch_rss(url)
            for entry in entries:
                if refined_count >= MAX_REFINE_PER_RUN:
                    break
                src = entry["url"]
                if not src:
                    continue
                if await database.source_url_exists(src):
                    log.info("skip: already exists %s", src)
                    continue
                if not rate.check_and_increment():
                    log.warning("Daily refine limit reached, stopping crawl for input %d", input_id)
                    break
                # Try fetching full article body; fall back to RSS summary on error
                try:
                    raw = await crawler.fetch_page(src, method="html")
                except Exception as exc:
                    log.warning("RSS body fetch failed (%s), falling back to summary: %s", exc, src)
                    raw = entry["summary"] or entry["title"]
                try:
                    refined = await get_llm().refine_content(raw, src, feed_name=feed_name, keyword=keyword)
                    if refined.get("skip"):
                        log.info("skip: filtered by LLM %s", src)
                        continue
                    await database.create_post(
                        input_id=input_id,
                        title=refined["title"],
                        content=refined["content"],
                        summary=refined["summary"],
                        tags=refined["tags"],
                        source_url=src,
                    )
                    refined_count += 1
                except Exception:
                    log.exception("Refine failed for %s", src)

        else:
            # html or playwright — extract article links from listing page, dedup per article
            article_links = await crawler.fetch_links(url)
            if not article_links:
                # Fallback: no links found, treat page itself as single article
                if await database.source_url_exists(url):
                    log.info("skip: already exists %s", url)
                elif not rate.check_and_increment():
                    log.warning("Daily refine limit reached, stopping crawl for input %d", input_id)
                else:
                    try:
                        raw = await crawler.fetch_page(url, method=method)
                        refined = await get_llm().refine_content(raw, url, feed_name=feed_name, keyword=keyword)
                        if not refined.get("skip"):
                            await database.create_post(
                                input_id=input_id,
                                title=refined["title"],
                                content=refined["content"],
                                summary=refined["summary"],
                                tags=refined["tags"],
                                source_url=url,
                            )
                            refined_count += 1
                        else:
                            log.info("skip: filtered by LLM %s", url)
                    except Exception:
                        log.exception("Refine failed for %s", url)
            else:
                for article_url in article_links:
                    if refined_count >= MAX_REFINE_PER_RUN:
                        break
                    if await database.source_url_exists(article_url):
                        log.info("skip: already exists %s", article_url)
                        continue
                    if not rate.check_and_increment():
                        log.warning("Daily refine limit reached, stopping crawl for input %d", input_id)
                        break
                    try:
                        raw = await crawler.fetch_page(article_url, method=method)
                        refined = await get_llm().refine_content(raw, article_url, feed_name=feed_name, keyword=keyword)
                        if refined.get("skip"):
                            log.info("skip: filtered by LLM %s", article_url)
                            continue
                        await database.create_post(
                            input_id=input_id,
                            title=refined["title"],
                            content=refined["content"],
                            summary=refined["summary"],
                            tags=refined["tags"],
                            source_url=article_url,
                        )
                        refined_count += 1
                    except Exception:
                        log.exception("Refine failed for %s", article_url)

        hours = INTERVAL_MAP.get(inp["crawl_interval"], 6)
        await database.update_input(
            input_id,
            status="active",
            last_crawl_at=datetime.utcnow().isoformat(),
            next_crawl_at=(datetime.utcnow() + timedelta(hours=hours)).isoformat(),
        )
        if refined_count > 0:
            log.info("Crawl done for input %d: %d items saved", input_id, refined_count)
        else:
            log.info("Crawl done for input %d: no new items (skipped or filtered)", input_id)

    except Exception:
        log.exception("Crawl failed for input %d", input_id)
        await database.update_input(input_id, status="failed")


def schedule_input(input_id: int, interval: str) -> None:
    hours = INTERVAL_MAP.get(interval, 6)
    job_id = f"crawl_{input_id}"
    scheduler.add_job(
        crawl_input,
        IntervalTrigger(hours=hours),
        id=job_id,
        args=[input_id],
        replace_existing=True,
    )


def unschedule_input(input_id: int) -> None:
    job_id = f"crawl_{input_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def get_scheduler_status() -> dict:
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "job_count": len(jobs),
        "jobs": [
            {
                "id": j.id,
                "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
            }
            for j in jobs
        ],
    }
