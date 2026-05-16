import asyncio
import bcrypt
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import scheduler as sched
import rate
from llm.factory import get_llm
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    sched.scheduler.start()
    inputs = await database.get_inputs()
    for inp in inputs:
        if inp["status"] == "active":
            sched.schedule_input(inp["id"], inp["crawl_interval"])
    yield
    sched.scheduler.shutdown()


app = FastAPI(title="crawl-blog API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- auth helpers ---

def verify_password(plain: str) -> bool:
    return bcrypt.checkpw(plain.encode(), settings.password_hash.encode())


async def check_rate_limit(request: Request):
    ip = request.client.host
    rl = await database.get_rate_limit(ip)
    if rl and rl["locked_until"]:
        locked_until = datetime.fromisoformat(rl["locked_until"])
        if datetime.utcnow() < locked_until:
            raise HTTPException(status_code=429, detail="IP locked due to too many failed attempts")
        await database.reset_fails(ip)


async def auth_request(request: Request, password: str) -> None:
    await check_rate_limit(request)
    if not verify_password(password):
        ip = request.client.host
        count = await database.record_fail(ip)
        if count >= 5:
            await database.lock_ip(ip, datetime.utcnow() + timedelta(minutes=15))
        raise HTTPException(status_code=401, detail="Invalid password")
    await database.reset_fails(request.client.host)


# --- schemas ---

class InputCreate(BaseModel):
    value: str
    password: str
    interval: str = "6h"


class IntervalUpdate(BaseModel):
    interval: str
    password: str


class DeleteRequest(BaseModel):
    password: str


class CrawlTrigger(BaseModel):
    password: str


# --- inputs ---

@app.post("/api/inputs", status_code=201)
async def create_input(body: InputCreate, request: Request):
    await auth_request(request, body.password)

    url = body.value.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    input_id = await database.create_input(url, "url", body.interval)

    judgment = await get_llm().judge_input(url)
    approved = judgment.get("approved", False)
    status = "active" if approved else "rejected"

    await database.update_input(
        input_id,
        status=status,
        claude_approved=1 if approved else 0,
        claude_reason=judgment.get("reason"),
        crawl_method=judgment.get("crawl_method"),
    )

    if approved:
        sched.schedule_input(input_id, body.interval)

    return {"id": input_id, "approved": approved, "judgment": judgment}


@app.get("/api/inputs")
async def list_inputs():
    return await database.get_inputs()


@app.delete("/api/inputs/{input_id}")
async def delete_input(input_id: int, body: DeleteRequest, request: Request):
    await auth_request(request, body.password)
    inp = await database.get_input(input_id)
    if not inp:
        raise HTTPException(status_code=404, detail="Input not found")
    await database.delete_input(input_id)
    sched.unschedule_input(input_id)
    return {"ok": True}


@app.patch("/api/inputs/{input_id}")
async def update_interval(input_id: int, body: IntervalUpdate, request: Request):
    await auth_request(request, body.password)
    if body.interval not in ("1h", "6h", "24h"):
        raise HTTPException(status_code=400, detail="Invalid interval")
    inp = await database.get_input(input_id)
    if not inp:
        raise HTTPException(status_code=404, detail="Input not found")
    await database.update_input(input_id, crawl_interval=body.interval)
    if inp["status"] == "active":
        sched.schedule_input(input_id, body.interval)
    return {"ok": True}


# --- posts ---

@app.get("/api/posts")
async def list_posts(
    input_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
):
    return await database.get_posts(input_id=input_id, search=search, page=page, per_page=per_page)


@app.get("/api/posts/{post_id}")
async def get_post(post_id: int):
    post = await database.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.patch("/api/posts/{post_id}/read")
async def mark_read(post_id: int):
    await database.mark_read(post_id)
    return {"ok": True}


# --- status ---

@app.get("/api/status")
async def get_status():
    inputs = await database.get_inputs()
    active = [i for i in inputs if i["status"] == "active"]
    failed = [i for i in inputs if i["status"] == "failed"]
    last_crawl = max(
        (i["last_crawl_at"] for i in inputs if i["last_crawl_at"]), default=None
    )

    overall = "normal"
    if not active:
        overall = "stopped"
    elif failed:
        overall = "warning"

    return {
        "overall": overall,
        "active_count": len(active),
        "llm_remaining": rate.remaining(),
        "scheduler": sched.get_scheduler_status(),
        "last_crawl_at": last_crawl,
    }


# --- crawl trigger ---

@app.post("/api/crawl/{input_id}")
async def trigger_crawl(input_id: int, body: CrawlTrigger, request: Request):
    await auth_request(request, body.password)
    inp = await database.get_input(input_id)
    if not inp:
        raise HTTPException(status_code=404, detail="Input not found")
    if inp["status"] == "crawling":
        raise HTTPException(status_code=409, detail="Already crawling")
    asyncio.create_task(sched.crawl_input(input_id))
    return {"ok": True}
