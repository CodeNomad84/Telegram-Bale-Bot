"""Channel membership check."""

# from bot_instance import bot
# from config import CHANNEL_ID

# # Status values that count as "joined" across Bale/Telegram-style APIs.
# ACCEPTED = ("member", "administrator", "creator", "owner")


# async def is_member(user_id):
#     """True if the user is in the channel. No channel configured means no gate."""
#     if not CHANNEL_ID:
#         return True
#     try:
#         member = await bot.get_chat_member(CHANNEL_ID, user_id)
#     except Exception:
#         # Treat API/network failures as "not joined" so the gate is not bypassed.
#         return False
#     return getattr(member, "status", None) in ACCEPTED

"""Channel membership check with debug logging."""

from bot_instance import bot
from config import CHANNEL_ID

# وضعیت‌هایی که نشان‌دهنده عضویت هستند
ACCEPTED = ("member", "administrator", "creator", "owner")


async def is_member(user_id):
    """بررسی عضویت کاربر در کانال."""
    if not CHANNEL_ID:
        print("[DEBUG] No channel ID set, skipping membership check.")
        return True

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        status = getattr(member, "status", None)
        print(f"[DEBUG] is_member: user_id={user_id}, status='{status}'")
        return status in ACCEPTED
    except Exception as e:
        print(f"[ERROR] is_member failed: {e}")
        # در صورت بروز خطا، فرض می‌کنیم کاربر عضو نیست تا امنیت حفظ شود
        return False