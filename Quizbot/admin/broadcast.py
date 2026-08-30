import asyncio
from database.db import get_all_user_ids, log_admin_action
from bot_instance import bot


async def broadcast_send(admin_id, text):
    """Send a text message to all users."""
    user_ids = await get_all_user_ids()
    total = len(user_ids)
    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Prevent rate limiting

    await log_admin_action(admin_id, "broadcast", f"sent to {sent} users, failed {failed}")
    return sent, failed


async def get_all_user_ids():
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cursor.fetchall()]