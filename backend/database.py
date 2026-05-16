import aiomysql
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from settings import settings

CREATE_INPUTS = """
CREATE TABLE IF NOT EXISTS inputs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    keyword TEXT,
    value TEXT NOT NULL,
    type VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    claude_approved TINYINT,
    claude_reason TEXT,
    crawl_method VARCHAR(20),
    crawl_interval VARCHAR(5) NOT NULL DEFAULT '6h',
    last_crawl_at VARCHAR(32),
    next_crawl_at VARCHAR(32),
    post_count INT NOT NULL DEFAULT 0,
    has_new TINYINT NOT NULL DEFAULT 0,
    created_at VARCHAR(32) NOT NULL DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%dT%H:%i:%S'))
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
"""

CREATE_POSTS = """
CREATE TABLE IF NOT EXISTS posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    input_id INT NOT NULL,
    title TEXT NOT NULL,
    content LONGTEXT NOT NULL,
    summary TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    source_url TEXT,
    is_read TINYINT NOT NULL DEFAULT 0,
    is_new TINYINT NOT NULL DEFAULT 1,
    created_at VARCHAR(32) NOT NULL DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%dT%H:%i:%S')),
    FOREIGN KEY (input_id) REFERENCES inputs(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
"""

CREATE_RATE_LIMITS = """
CREATE TABLE IF NOT EXISTS rate_limits (
    ip VARCHAR(64) PRIMARY KEY,
    fail_count INT NOT NULL DEFAULT 0,
    locked_until VARCHAR(32)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
"""


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiomysql.Connection, None]:
    conn = await aiomysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
        charset="utf8mb4",
        cursorclass=aiomysql.DictCursor,
        autocommit=False,
    )
    try:
        yield conn
    finally:
        conn.close()


async def init_db():
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(CREATE_INPUTS)
            await cur.execute(CREATE_POSTS)
            await cur.execute(CREATE_RATE_LIMITS)
        await conn.commit()


# --- inputs ---

async def create_input(value: str, input_type: str, interval: str = "6h", name: str | None = None, keyword: str | None = None) -> int:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO inputs (value, type, crawl_interval, name, keyword) VALUES (%s, %s, %s, %s, %s)",
                (value, input_type, interval, name, keyword),
            )
            last_id = cur.lastrowid
        await conn.commit()
        return last_id


async def get_inputs() -> list[dict]:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT * FROM inputs WHERE status != 'deleted' ORDER BY created_at DESC"
            )
            return await cur.fetchall()


async def get_input(input_id: int) -> dict | None:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM inputs WHERE id = %s", (input_id,))
            return await cur.fetchone()


async def update_input(input_id: int, **fields) -> None:
    if not fields:
        return
    cols = ", ".join(f"{k} = %s" for k in fields)
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"UPDATE inputs SET {cols} WHERE id = %s",
                (*fields.values(), input_id),
            )
        await conn.commit()


async def delete_input(input_id: int) -> None:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE inputs SET status = 'deleted' WHERE id = %s", (input_id,)
            )
        await conn.commit()


# --- posts ---

async def create_post(
    input_id: int, title: str, content: str, summary: str, tags: list[str], source_url: str
) -> int:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO posts (input_id, title, content, summary, tags, source_url) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (input_id, title, content, summary, json.dumps(tags, ensure_ascii=False), source_url),
            )
            last_id = cur.lastrowid
            await cur.execute(
                "UPDATE inputs SET post_count = post_count + 1, has_new = 1 WHERE id = %s",
                (input_id,),
            )
        await conn.commit()
        return last_id


async def get_posts(
    input_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    wheres = ["1=1"]
    params: list = []

    if input_id is not None:
        wheres.append("input_id = %s")
        params.append(input_id)
    if search:
        wheres.append("(title LIKE %s OR content LIKE %s)")
        params += [f"%{search}%", f"%{search}%"]

    where = " AND ".join(wheres)
    offset = (page - 1) * per_page

    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"SELECT COUNT(*) as cnt FROM posts WHERE {where}", params)
            row = await cur.fetchone()
            total = row["cnt"]

            await cur.execute(
                f"SELECT * FROM posts WHERE {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
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
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
            row = await cur.fetchone()
    if not row:
        return None
    p = dict(row)
    p["tags"] = json.loads(p["tags"])
    return p


async def source_url_exists(source_url: str) -> bool:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1 FROM posts WHERE source_url = %s LIMIT 1", (source_url,))
            return await cur.fetchone() is not None


async def mark_read(post_id: int) -> None:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE posts SET is_read = 1, is_new = 0 WHERE id = %s", (post_id,)
            )
        await conn.commit()


# --- rate limiting ---

async def get_rate_limit(ip: str) -> dict | None:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM rate_limits WHERE ip = %s", (ip,))
            return await cur.fetchone()


async def record_fail(ip: str) -> int:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO rate_limits (ip, fail_count) VALUES (%s, 1) "
                "ON DUPLICATE KEY UPDATE fail_count = fail_count + 1",
                (ip,),
            )
            await cur.execute("SELECT fail_count FROM rate_limits WHERE ip = %s", (ip,))
            row = await cur.fetchone()
        await conn.commit()
        return row["fail_count"]


async def lock_ip(ip: str, until: datetime) -> None:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE rate_limits SET locked_until = %s WHERE ip = %s",
                (until.isoformat(), ip),
            )
        await conn.commit()


async def reset_fails(ip: str) -> None:
    async with get_db() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE rate_limits SET fail_count = 0, locked_until = NULL WHERE ip = %s",
                (ip,),
            )
        await conn.commit()
