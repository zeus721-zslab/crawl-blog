import logging
from datetime import datetime, timedelta

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import database
import crawler
from llm.factory import get_llm
import rate

log = logging.getLogger(__name__)

INTERVAL_MAP = {"1h": 1, "6h": 6, "24h": 24}
MAX_REFINE_PER_RUN = 3  # Sonnet refine cap per crawl run

_jobstores = {
    "default": SQLAlchemyJobStore(url="sqlite:////app/data/jobs.db")
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

    try:
        method = inp["crawl_method"] or "html"
        url = inp["value"]

        if method == "rss":
            entries = await crawler.fetch_rss(url)
            for entry in entries:
                if refined_count >= MAX_REFINE_PER_RUN:
                    break
                src = entry["url"]
                if not src or await database.source_url_exists(src):
                    continue
                if not rate.check_and_increment():
                    log.warning("Daily refine limit reached, stopping crawl for input %d", input_id)
                    break
                raw = entry["summary"] or entry["title"]
                try:
                    refined = await get_llm().refine_content(raw, src)
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
            # html or playwright — URL itself is the article
            if await database.source_url_exists(url):
                log.debug("source_url already collected, skipping: %s", url)
            elif not rate.check_and_increment():
                log.warning("Daily refine limit reached, stopping crawl for input %d", input_id)
            else:
                try:
                    raw = await crawler.fetch_page(url, method=method)
                    refined = await get_llm().refine_content(raw, url)
                    await database.create_post(
                        input_id=input_id,
                        title=refined["title"],
                        content=refined["content"],
                        summary=refined["summary"],
                        tags=refined["tags"],
                        source_url=url,
                    )
                    refined_count += 1
                except Exception:
                    log.exception("Refine failed for %s", url)

        hours = INTERVAL_MAP.get(inp["crawl_interval"], 6)
        await database.update_input(
            input_id,
            status="active",
            last_crawl_at=datetime.utcnow().isoformat(),
            next_crawl_at=(datetime.utcnow() + timedelta(hours=hours)).isoformat(),
        )
        log.info("Crawl done for input %d: %d items refined", input_id, refined_count)

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
