from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import asyncio
import database
import crawler
from llm.factory import get_llm

scheduler = AsyncIOScheduler()

INTERVAL_MAP = {"1h": 1, "6h": 6, "24h": 24}


async def crawl_input(input_id: int) -> None:
    inp = await database.get_input(input_id)
    if not inp or inp["status"] == "deleted":
        return

    await database.update_input(input_id, status="crawling")
    try:
        method = inp["crawl_method"] or "html"
        value = inp["value"]

        if method == "rss":
            entries = await crawler.fetch_rss(value)
            for entry in entries:
                raw = entry["summary"] or entry["title"]
                refined = await get_llm().refine_content(raw, entry["url"])
                await database.create_post(
                    input_id=input_id,
                    title=refined["title"],
                    content=refined["content"],
                    summary=refined["summary"],
                    tags=refined["tags"],
                    source_url=entry["url"],
                )
        else:
            urls = [value] if inp["type"] == "url" else await crawler.search_and_fetch(value)
            for url in urls[:3]:
                raw = await crawler.fetch_html(url)
                refined = await get_llm().refine_content(raw, url)
                await database.create_post(
                    input_id=input_id,
                    title=refined["title"],
                    content=refined["content"],
                    summary=refined["summary"],
                    tags=refined["tags"],
                    source_url=url,
                )

        hours = INTERVAL_MAP.get(inp["crawl_interval"], 6)
        await database.update_input(
            input_id,
            status="active",
            last_crawl_at=datetime.utcnow().isoformat(),
            next_crawl_at=(datetime.utcnow() + timedelta(hours=hours)).isoformat(),
        )
    except Exception as e:
        await database.update_input(input_id, status="failed")
        raise


def schedule_input(input_id: int, interval: str) -> None:
    hours = INTERVAL_MAP.get(interval, 6)
    job_id = f"crawl_{input_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
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
