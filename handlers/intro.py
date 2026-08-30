"""Intro questions: marital status and (parents only) children gender."""

import asyncio

from bot_instance import bot
from data.content import INTRO, INTRO_ORDER
from database.db import get_user, update_user
from handlers.states import STATE_INTRO
from keyboards.builders import choice_keyboard

LABELS = ["الف", "ب", "ج", "د", "ه"]


async def start_intro(user_id):
    await update_user(user_id, state=STATE_INTRO, step=0, product_keys=[])
    await send_intro_question(user_id, 0)


async def send_intro_question(user_id, index):
    key = INTRO_ORDER[index]
    question = INTRO[key]
    options = question["options"]
    options_text = "\n".join(f"{LABELS[i]}) {opt['text']}" for i, opt in enumerate(options))
    full_text = question["text"] + "\n\n" + options_text + "\n\n👇 یکی را انتخاب کنید:"
    labels = LABELS[:len(options)]
    await bot.send_message(
        user_id,
        text=full_text,
        reply_markup=choice_keyboard("intro", index, labels)
    )


async def handle_intro_answer(user_id, index, option_index):
    """Intro answers only build the context; they never contribute quiz scores."""
    key = INTRO_ORDER[index]
    options = INTRO[key]["options"]
    if not 0 <= option_index < len(options):
        return False
    option = options[option_index]

    user = await get_user(user_id)
    product_keys = list(user["product_keys"])
    if option["product_key"] and option["product_key"] not in product_keys:
        product_keys.append(option["product_key"])

    fields = {"product_keys": product_keys}
    for field in ("role", "gender", "children"):
        if option[field]:
            fields[field] = option[field]
    await update_user(user_id, **fields)

    # Singles skip the children question and go straight to the quiz.
    is_parent = (fields.get("role") or user["role"]) in ("mother", "father")
    if index == 0 and is_parent:
        await update_user(user_id, step=1)
        # ارسال پیام تأیید قبل از سوال بعدی
        await bot.send_message(user_id, "✅ پاسخ شما ثبت شد.")
        await asyncio.sleep(0.3)
        await send_intro_question(user_id, 1)
        return True

    from handlers.quiz import start_quiz
    # ارسال پیام تأیید قبل از شروع آزمون
    await bot.send_message(user_id, "✅ پاسخ شما ثبت شد.")
    await asyncio.sleep(0.3)
    await start_quiz(user_id)
    return True