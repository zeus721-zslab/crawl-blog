import aiosqlite
import json
from datetime import datetime

DB_PATH = "/app/data/crawl-blog.db"

CREATE_INPUTS = """
CREATE TABLE IF NOT EXISTS inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('keyword', 'url')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('active', 'crawling', 'failed', 'rejected', 'deleted')),
    claude_approved INTEGER,
    claude_reason TEXT,
    crawl_method TEXT,
    crawl_interval TEXT NOT NULL DEFAULT '6h' CHECK(crawl_interval IN ('1h', '6h', '24h')),
    last_crawl_at TEXT,
    next_crawl_at TEXT,
    post_count INTEGER NOT NULL DEFAULT 0,
    has_new INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

CREATE_POSTS = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_id INTEGER NOT NULL REFERENCES inputs(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    source_url TEXT,
    is_read INTEGER NOT NULL DEFAULT 0,
    is_new INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

CREATE_RATE_LIMITS = """
CREATE TABLE IF NOT EXISTS rate_limits (
    ip TEXT PRIMARY KEY,
    fail_count INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT
)
"""


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db():
    async with await get_db() as db:
        await db.execute(CREATE_INPUTS)
        await db.execute(CREATE_POSTS)
        await db.execute(CREATE_RATE_LIMITS)
        await db.commit()


# --- inputs ---

async def create_input(value: str, input_type: str, interval: str = "6h") -> int:
    async with await get_db() as db:
        cur = await db.execute(
            "INSERT INTO inputs (value, type, crawl_interval) VALUES (?, ?, ?)",
            (value, input_type, interval),
        )
        await db.commit()
        return cur.lastrowid


async def get_inputs() -> list[dict]:
    async with await get_db() as db:
        cur = await db.execute(
            "SELECT * FROM inputs WHERE status != 'deleted' ORDER BY created_at DESC"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_input(input_id: int) -> dict | None:
    async with await get_db() as db:
        cur = await db.execute("SELECT * FROM inputs WHERE id = ?", (input_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_input(input_id: int, **fields) -> None:
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    async with await get_db() as db:
        await db.execute(
            f"UPDATE inputs SET {cols} WHERE id = ?",
            (*fields.values(), input_id),
        )
        await db.commit()


async def delete_input(input_id: int) -> None:
    async with await get_db() as db:
        await db.execute(
            "UPDATE inputs SET status = 'deleted' WHERE id = ?", (input_id,)
        )
        await db.commit()


# --- posts ---

async def create_post(
    input_id: int, title: str, content: str, summary: str, tags: list[str], source_url: str
) -> int:
    async with await get_db() as db:
        cur = await db.execute(
            "INSERT INTO posts (input_id, title, content, summary, tags, source_url) VALUES (?, ?, ?, ?, ?, ?)",
            (input_id, title, content, summary, json.dumps(tags, ensure_ascii=False), source_url),
        )
        await db.execute(
            "UPDATE inputs SET post_count = post_count + 1, has_new = 1 WHERE id = ?",
            (input_id,),
        )
        await db.commit()
        return cur.lastrowid


async def get_posts(
    input_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    wheres = ["1=1"]
    params: list = []

    if input_id is not None:
        wheres.append("input_id = ?")
        params.append(input_id)
    if search:
        wheres.append("(title LIKE ? OR content LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]

    where = " AND ".join(wheres)
    offset = (page - 1) * per_page

    async with await get_db() as db:
        cur = await db.execute(f"SELECT COUNT(*) FROM posts WHERE {where}", params)
        total = (await cur.fetchone())[0]

        cur = await db.execute(
            f"SELECT * FROM posts WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [*params, per_page, offset],
        )
        rows = await cur.fetchall()

    posts = []
    for r in rows:
        p = dict(r)
        p["tags"] = json.loads(p["tags"])
        posts.append(p)

    return {"total": total, "page": page, "per_page": per_page, "posts": posts}


async def get_post(post_id: int) -> dict | None:
    async with await get_db() as db:
        cur = await db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = await cur.fetchone()
        if not row:
            return None
        p = dict(row)
        p["tags"] = json.loads(p["tags"])
        return p


async def mark_read(post_id: int) -> None:
    async with await get_db() as db:
        await db.execute(
            "UPDATE posts SET is_read = 1, is_new = 0 WHERE id = ?", (post_id,)
        )
        await db.commit()


# --- rate limiting ---

async def get_rate_limit(ip: str) -> dict | None:
    async with await get_db() as db:
        cur = await db.execute("SELECT * FROM rate_limits WHERE ip = ?", (ip,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def record_fail(ip: str) -> int:
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO rate_limits (ip, fail_count) VALUES (?, 1) "
            "ON CONFLICT(ip) DO UPDATE SET fail_count = fail_count + 1",
            (ip,),
        )
        await db.commit()
        cur = await db.execute("SELECT fail_count FROM rate_limits WHERE ip = ?", (ip,))
        row = await cur.fetchone()
        return row[0]


async def lock_ip(ip: str, until: datetime) -> None:
    async with await get_db() as db:
        await db.execute(
            "UPDATE rate_limits SET locked_until = ? WHERE ip = ?",
            (until.isoformat(), ip),
        )
        await db.commit()


async def reset_fails(ip: str) -> None:
    async with await get_db() as db:
        await db.execute(
            "UPDATE rate_limits SET fail_count = 0, locked_until = NULL WHERE ip = ?",
            (ip,),
        )
        await db.commit()
