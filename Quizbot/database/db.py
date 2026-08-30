"""یک schema یکدست؛ همهٔ اطلاعات کاربر در جدول users."""

import csv
import json
from datetime import datetime

import aiosqlite

from config import DB_DIR, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id      INTEGER PRIMARY KEY,
    username     TEXT,
    display_name TEXT,
    phone        TEXT,
    role         TEXT,
    gender       TEXT,
    children     TEXT,
    product_keys TEXT,
    answers      TEXT NOT NULL DEFAULT '[]',
    result_code  INTEGER,
    result_title TEXT,
    state        TEXT NOT NULL DEFAULT 'new',
    step         INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invites (
    inviter_id INTEGER PRIMARY KEY,
    count      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS invited_users (
    invited_id INTEGER PRIMARY KEY,
    inviter_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id   INTEGER NOT NULL,
    action     TEXT NOT NULL,
    details    TEXT,
    created_at TEXT NOT NULL
);
"""


def _now():
    return datetime.now().isoformat(timespec="seconds")


async def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def ensure_user(user_id, display_name=None):
    """کاربر را می‌سازد یا نام نمایشی گرفته‌شده از بله را به‌روز می‌کند."""
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, display_name, created_at, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   display_name = COALESCE(NULLIF(excluded.display_name, ''), users.display_name),
                   updated_at   = excluded.updated_at""",
            (user_id, display_name or "", now, now),
        )
        await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return None
    user = dict(row)
    user["answers"] = json.loads(user["answers"] or "[]")
    user["product_keys"] = json.loads(user["product_keys"] or "[]")
    return user


async def update_user(user_id, **fields):
    if not fields:
        return
    if "answers" in fields:
        fields["answers"] = json.dumps(fields["answers"], ensure_ascii=False)
    if "product_keys" in fields:
        fields["product_keys"] = json.dumps(fields["product_keys"], ensure_ascii=False)
    fields["updated_at"] = _now()
    assignments = ", ".join(f"{key} = ?" for key in fields)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {assignments} WHERE user_id = ?",
            (*fields.values(), user_id),
        )
        await db.commit()


async def reset_quiz(user_id):
    await update_user(
        user_id,
        role=None,
        gender=None,
        children=None,
        product_keys=[],
        answers=[],
        result_code=None,
        result_title=None,
        step=0,
    )


async def register_invite(inviter_id, invited_id):
    """هر کاربر فقط یک‌بار برای یک معرف شمرده می‌شود."""
    if inviter_id == invited_id:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM invited_users WHERE invited_id = ?", (invited_id,)
        ) as cursor:
            if await cursor.fetchone():
                return False
        await db.execute(
            "INSERT INTO invited_users (invited_id, inviter_id) VALUES (?, ?)",
            (invited_id, inviter_id),
        )
        await db.execute(
            """INSERT INTO invites (inviter_id, count) VALUES (?, 1)
               ON CONFLICT(inviter_id) DO UPDATE SET count = count + 1""",
            (inviter_id,),
        )
        await db.commit()
    return True


async def get_invite_count(inviter_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT count FROM invites WHERE inviter_id = ?", (inviter_id,)
        ) as cursor:
            row = await cursor.fetchone()
    return row[0] if row else 0


async def export_users_csv(path):
    """پشتیبان متنی برای قرعه‌کشی و پیام‌های گروهی."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT user_id, username, display_name, phone, role, gender, children,
                      result_code, result_title, state, updated_at
               FROM users ORDER BY updated_at DESC"""
        ) as cursor:
            rows = [dict(row) async for row in cursor]
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else ["user_id"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


async def get_all_user_ids():
    """بازگرداندن لیست تمام user_id های ثبت‌شده."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cursor.fetchall()]


# ----- Admin logs -----
async def log_admin_action(admin_id, action, details=None):
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO admin_logs (admin_id, action, details, created_at) VALUES (?, ?, ?, ?)",
            (admin_id, action, details, now),
        )
        await db.commit()


async def get_admin_logs(limit=100):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            return [dict(row) async for row in cursor]