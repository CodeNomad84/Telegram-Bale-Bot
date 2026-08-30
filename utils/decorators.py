from functools import wraps
from config import ADMIN_IDS
from bot_instance import bot


def admin_required(func):
    @wraps(func)
    async def wrapper(callback_query, *args, **kwargs):
        user_id = callback_query.author.id
        if user_id not in ADMIN_IDS:
            await callback_query.answer("⛔ شما دسترسی ادمین ندارید.", show_alert=True)
            return
        return await func(callback_query, *args, **kwargs)
    return wrapper


def admin_message_required(func):
    @wraps(func)
    async def wrapper(message, *args, **kwargs):
        user_id = message.author.id
        if user_id not in ADMIN_IDS:
            await bot.send_message(user_id, "⛔ شما دسترسی ادمین ندارید.")
            return
        return await func(message, *args, **kwargs)
    return wrapper