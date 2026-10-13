"""Final output: personality description, then image, then product suggestion."""

import os
import random
from collections import Counter

from bot_instance import bot
from config import BOT_USERNAME, INVITE_IMAGE, NO_ANSWERS_TEXT, PICS_DIR
from data.content import PRODUCTS, RESULT_IMAGES, RESULT_TEXTS
from database.db import get_user, update_user
from handlers.states import STATE_DONE
from keyboards.builders import finish_keyboard


def compute_code(answers):
    """Most frequent code wins; ties are broken randomly among the leaders."""
    codes = [code for code in answers if code]
    if not codes:
        return None
    counter = Counter(codes)
    top = max(counter.values())
    return random.choice([code for code, count in counter.items() if count == top])


def invite_link(user_id):
    """Deep link that credits this user as the inviter."""
    return f"https://ble.ir/{BOT_USERNAME.lstrip('@')}?start={user_id}"
    


def build_description(code):
    """Heading with title and nickname, followed by the RESULT_TEXTS description."""
    result = RESULT_TEXTS.get(code, {})
    title = result.get("title", "")
    nickname = result.get("nickname", "")
    heading = f"🎯 سبک تربیتی تو: {title}"
    if nickname:
        heading += f" «{nickname}»"
    return f"{heading}\n\n{result.get('description', '')}".strip()


def build_products(product_keys):
    """Product suggestions collected from the intro answers."""
    lines = []
    for key in product_keys:
        product = PRODUCTS.get(key)
        if product and product["url"]:
            lines.append(f"🔹 {product['name']}\n{product['url']}")
    if not lines:
        return ""
    return "🎁 پیشنهاد ما برای تو:\n\n" + "\n\n".join(lines)


def result_image_path(code, user):
    """Gendered image (_female/_male) if it exists, else the base image, else None."""
    base_image = RESULT_IMAGES.get(code, "")
    if not base_image:
        return None
    role = user.get("role")
    gender = user.get("gender")
    gender_suffix = None
    if role == "single" and gender in ("girl", "female", "boy", "male"):
        # برای مجردها از جنسیت خودش استفاده کن
        gender_suffix = "female" if gender in ("girl", "female") else "male"
    elif role in ("mother", "father"):
        # برای والدین از نقش استفاده کن
        gender_suffix = "female" if role == "mother" else "male"

    candidates = []
    if gender_suffix:
        name, ext = os.path.splitext(base_image)
        candidates.append(f"{name}_{gender_suffix}{ext}")
    candidates.append(base_image)  # fallback به تصویر اصلی
    for image_name in candidates:
        path = PICS_DIR / image_name
        if path.exists():
            return path
    return None


async def send_result(user_id):
    """Send the result in fixed order: description, image, product suggestion."""
    user = await get_user(user_id)
    code = compute_code(user["answers"])
    if code is None:
        await bot.send_message(user_id, text=NO_ANSWERS_TEXT)
        return

    result = RESULT_TEXTS.get(code, {})
    await update_user(
        user_id,
        result_code=code,
        result_title=result.get("title", ""),
        state=STATE_DONE,
    )

    # 1+2) Personality type image with the description as caption;
    # without an image the description is still sent as plain text.
    description = build_description(code)
    image_path = result_image_path(code, user)
    if image_path:
        with open(image_path, "rb") as photo:
            await bot.send_photo(user_id, photo=photo, caption=description)
    else:
        await bot.send_message(user_id, text=description)

    # 3) Product suggestion
    products_text = build_products(user["product_keys"])
    if products_text:
        await bot.send_message(user_id, text=products_text)

    # Referral invitation
    link = invite_link(user_id)
    invite_text = (
"🧩* مجرد یا متاهل فرقی نداره*، بیاید بهتون بگیم سبک تربیتی شما چیه 😉\n\n\n"
"اگر میخوای تو برنده این قسمت باشی، با پیوند اختصاصی خودت دوستان بیشتری رو به این بازی دعوت کن 💌\n\n"
"همراه با جوایز ویژه 😍🎁\n"
"*نفر اول ۳ میلیون و یک دوره رایگان*\n"
"*نفر دوم ۲ میلیون و یک دوره رایگان*\n"
"*نفر سوم ۱ میلیون و یک دوره رایگان*\n\n\n"
 f"{link}"

    )
    if INVITE_IMAGE.exists():
        with open(INVITE_IMAGE, "rb") as photo:
            await bot.send_photo(
                user_id, photo=photo, caption=invite_text, reply_markup=finish_keyboard(link)
            )
    else:
        await bot.send_message(user_id, text=invite_text, reply_markup=finish_keyboard(link))
# # 4) Prize message with keyboard (copy link and restart)
#     prize_text = (
#         "اگر میخوای تو برنده این قسمت باشی، دوستان بیشتری رو به این بازی دعوت کن 💌\n"
#         "همراه با جوایز ویژه 😍🎁 \n"
#         "*نفر اول ۳ میلیون*\n"
#         "*نفر دوم ۲ میلیون*\n"
#         "*نفر سوم ۱ میلیون*\n"
#         "*نفر چهارم کتاب تربیت بر مدار فطرت*\n"
#         "*نفر پنجم یک دوره ارزنده رایگان*")
#     await bot.send_message(user_id, text=prize_text, reply_markup=finish_keyboard(link))