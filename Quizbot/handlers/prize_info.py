"""جمع‌آوری اطلاعات از برندگان قرعه‌کشی."""

from bot_instance import bot
from database.db import get_lottery_winner, save_winner_info


async def handle_winner_info(user_id, text):
    """
    اگر کاربر برنده جایزه است و اطلاعاتش را ثبت نکرده،
    متن ارسالی را به‌عنوان اطلاعات ذخیره می‌کند.
    """
    winner = await get_lottery_winner(user_id)
    if not winner:
        return False

    # اگر قبلاً ثبت کرده، دیگر کاری نکن
    if winner.get("info_text"):
        return False

    # ذخیره اطلاعات
    await save_winner_info(user_id, text)
    await bot.send_message(
        user_id,
        "✅ اطلاعات شما با موفقیت ثبت شد.\n"
        "سپاس از همراهی‌تان 🙏🌹\n\n"
        "در صورت نیاز به اصلاح، می‌توانید با پشتیبانی در تماس باشید."
    )
    return True