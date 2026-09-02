def to_persian_digits(number):
    """تبدیل اعداد انگلیسی به فارسی"""
    persian_map = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    return ''.join(persian_map.get(ch, ch) for ch in str(number))