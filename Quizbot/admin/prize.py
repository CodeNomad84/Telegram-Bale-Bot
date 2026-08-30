import asyncio
import re
import aiosqlite
from config import DB_PATH
from database.db import log_admin_action
from bot_instance import bot


async def prize_send(admin_id, criteria, message):
    """Send prize to users matching the criteria."""
    user_ids = await get_users_by_criteria(criteria)
    if not user_ids:
        await bot.send_message(admin_id, "هیچ کاربری با این معیارها یافت نشد.")
        return

    total = len(user_ids)
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, f"🎁 **پیام جایزه**\n\n{message}")
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)

    await log_admin_action(admin_id, "prize", f"sent to {sent} users (criteria: {criteria})")
    await bot.send_message(admin_id, f"جایزه به {sent} کاربر ارسال شد.")


async def get_users_by_criteria(criteria):
    """Return list of user_ids matching the criteria string."""
    # Example: "result_code=1" or "invites>=5"
    match = re.match(r"(\w+)\s*([=<>]+)\s*(\d+)", criteria.strip())
    if not match:
        return []

    field, op, value = match.groups()
    value = int(value)

    async with aiosqlite.connect(DB_PATH) as db:
        if field == "result_code":
            cursor = await db.execute(
                f"SELECT user_id FROM users WHERE result_code {op} ?", (value,)
            )
        elif field == "invites":
            # Get users with invite count >= value
            cursor = await db.execute(
                f"SELECT inviter_id FROM invites WHERE count {op} ?", (value,)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        else:
            return []
        return [row[0] for row in await cursor.fetchall()]