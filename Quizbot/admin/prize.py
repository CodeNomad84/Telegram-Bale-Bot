"""Lottery functions and prize message sending."""

import asyncio
import aiosqlite

from config import DB_PATH
from database.db import log_admin_action, register_lottery_winner
from bot_instance import bot

# پیش‌فرض تعداد برندگان برای هر دسته
DEFAULT_COUNTS = {
    "top_inviters": 5,
    "random_participants": 10,
    "random_inviters": 5,
}

CATEGORY_NAMES = {
    "top_inviters": "🏆 بالاترین دعوت‌کنندگان",
    "random_participants": "🎯 شرکت‌کنندگان تصادفی",
    "random_inviters": "🎁 دعوت‌کنندگان تصادفی",
}


async def lottery_top_inviters(count):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT inviter_id FROM invites ORDER BY count DESC LIMIT ?", (count,)
        )
        return [row[0] for row in await cursor.fetchall()]


async def lottery_random_participants(count):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE state = 'done' ORDER BY RANDOM() LIMIT ?",
            (count,)
        )
        return [row[0] for row in await cursor.fetchall()]


async def lottery_random_inviters(count):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT inviter_id FROM invites ORDER BY RANDOM() LIMIT ?", (count,)
        )
        return [row[0] for row in await cursor.fetchall()]


async def run_lottery(category, count):
    if category == "top_inviters":
        return await lottery_top_inviters(count)
    elif category == "random_participants":
        return await lottery_random_participants(count)
    elif category == "random_inviters":
        return await lottery_random_inviters(count)
    return []


async def get_users_info(user_ids):
    """اطلاعات کاربران به‌همراه تعداد دعوت؛ خروجی dict با کلید user_id (ترتیب ندارد)."""
    if not user_ids:
        return {}
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        placeholders = ",".join("?" * len(user_ids))
        cursor = await db.execute(
            f"""SELECT u.user_id, u.username, u.display_name, u.phone,
                       COALESCE(i.count, 0) AS invite_count
                FROM users u
                LEFT JOIN invites i ON i.inviter_id = u.user_id
                WHERE u.user_id IN ({placeholders})""",
            tuple(user_ids),
        )
        return {row["user_id"]: dict(row) async for row in cursor}


async def format_winners_list(user_ids, category):
    user_info = await get_users_info(user_ids)
    lines = [
        f"🎲 نتیجه قرعه‌کشی — {CATEGORY_NAMES.get(category, category)}",
        f"تعداد: {len(user_ids)} نفر\n",
    ]
    # پیمایش به ترتیب user_ids تا رتبه‌بندی قرعه‌کشی (مثلاً بیشترین دعوت) حفظ شود
    for i, uid in enumerate(user_ids, 1):
        row = user_info.get(uid, {})
        name = row.get("display_name") or row.get("username") or f"کاربر {uid}"
        line = f"{i}. {name} — 📨 {row.get('invite_count', 0)} دعوت"
        if row.get("phone"):
            line += f" — 📞 {row['phone']}"
        lines.append(line)
    return "\n".join(lines)


async def send_prize_message(admin_id, user_ids, message, category):
    """ارسال پیام جایزه و ثبت برندگان در دیتابیس."""
    sent_users = []
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, message)
            sent_users.append(uid)
            # ثبت برنده در دیتابیس
            await register_lottery_winner(uid, category)
        except Exception as e:
            print(f"[Prize] Failed to send to {uid}: {e}")
            failed += 1
        await asyncio.sleep(0.05)

    await log_admin_action(
        admin_id, "prize_message",
        f"category: {category}, sent: {len(sent_users)}, failed: {failed}"
    )
    return len(sent_users), failed