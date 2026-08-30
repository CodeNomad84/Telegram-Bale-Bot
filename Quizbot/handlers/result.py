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

    # 1) Personality type description
    await bot.send_message(user_id, text=build_description(code))

    # 2) Personality type image based on code AND gender (role)
    base_image = RESULT_IMAGES.get(code, "")
    if base_image:
        role = user.get("role")
        gender = user.get("gender")
        # تعیین جنسیت برای انتخاب تصویر
        if role == "single" and gender in ("girl", "female", "boy", "male"):
            # برای مجردها از جنسیت خودش استفاده کن
            gender_suffix = "female" if gender in ("girl", "female") else "male"
            name, ext = os.path.splitext(base_image)
            image_name = f"{name}_{gender_suffix}{ext}"
        elif role in ("mother", "father"):
            # برای والدین از نقش استفاده کن
            gender_suffix = "female" if role == "mother" else "male"
            name, ext = os.path.splitext(base_image)
            image_name = f"{name}_{gender_suffix}{ext}"
        else:
            image_name = base_image

    image_path = PICS_DIR / image_name if image_name else None
    if image_path and image_path.exists():
        with open(image_path, "rb") as photo:
            await bot.send_photo(user_id, photo=photo, caption=result.get("nickname", ""))
    else:
        # fallback به تصویر اصلی
        image_path = PICS_DIR / base_image if base_image else None
        if image_path and image_path.exists():
            with open(image_path, "rb") as photo:
                await bot.send_photo(user_id, photo=photo, caption=result.get("nickname", ""))

    # 3) Product suggestion
    products_text = build_products(user["product_keys"])
    if products_text:
        await bot.send_message(user_id, text=products_text)

    # Referral invitation
    link = invite_link(user_id)
    invite_text = (
        "این آزمون را برای دوستانت هم بفرست تا سبک تربیتی خودشان را بشناسند 💌\n\n"
        f"{link}"
    )
    if INVITE_IMAGE.exists():
        with open(INVITE_IMAGE, "rb") as photo:
            await bot.send_photo(
                user_id, photo=photo, caption=invite_text, reply_markup=finish_keyboard(link)
            )
    else:
        await bot.send_message(user_id, text=invite_text, reply_markup=finish_keyboard(link))