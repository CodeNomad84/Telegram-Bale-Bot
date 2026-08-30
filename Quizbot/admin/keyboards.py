from balethon.objects import InlineKeyboard

from config import CHANNEL_LINK


def join_keyboard():
    return InlineKeyboard(
        [{"text": "عضویت در کانال 🔗", "url": CHANNEL_LINK}],
        [{"text": "بررسی عضویت ✅", "callback_data": "check_join"}],
    )


def username_keyboard():
    return InlineKeyboard(
        [{"text": "بدون آیدی ادامه بده ➡️", "callback_data": "username:skip"}],
    )


def phone_keyboard():
    return InlineKeyboard(
        [{"text": "رد کردن شماره تماس ➡️", "callback_data": "phone:skip"}],
    )


def options_keyboard(prefix, options):
    """هر گزینه در یک ردیف؛ callback_data = prefix:index"""
    rows = [
        [{"text": text, "callback_data": f"{prefix}:{index}"}]
        for index, text in enumerate(options)
    ]
    return InlineKeyboard(*rows)


def finish_keyboard(invite_link):
    return InlineKeyboard(
        [{"text": "📋 رونوشت از لینک معرفی", "copy_text": {"text": invite_link}}],
        [{"text": "شروع مجدد 🔄", "callback_data": "restart"}],
    )


# ---------- Admin keyboards ----------
def admin_main_keyboard():
    return InlineKeyboard(
        [{"text": "📊 آمار", "callback_data": "admin:stats"}],
        [{"text": "📨 ارسال پیام همگانی", "callback_data": "admin:broadcast"}],
        [{"text": "📁 خروجی اکسل", "callback_data": "admin:export"}],
        [{"text": "📈 نمودار دعوت‌ها", "callback_data": "admin:graph"}],
        [{"text": "🎁 ارسال جایزه", "callback_data": "admin:prize"}],
        [{"text": "📋 لاگ‌ها", "callback_data": "admin:logs"}],
    )


def admin_back_keyboard():
    return InlineKeyboard(
        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "admin:main"}]
    )


def admin_cancel_keyboard():
    return InlineKeyboard(
        [{"text": "❌ لغو عملیات", "callback_data": "admin:cancel"}]
    )