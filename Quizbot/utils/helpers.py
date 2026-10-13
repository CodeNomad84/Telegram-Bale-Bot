def to_persian_digits(number):
    """تبدیل اعداد انگلیسی به فارسی"""
    persian_map = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    return ''.join(persian_map.get(ch, ch) for ch in str(number))


async def safe_answer(callback_query, text="", show_alert=False):
    """پاسخ به callback؛ خطای API (مثل «query is too old») ادامهٔ پردازش را متوقف نمی‌کند."""
    try:
        await callback_query.answer(text, show_alert=show_alert)
    except Exception as e:
        print(f"[WARNING] callback answer failed: {e}")