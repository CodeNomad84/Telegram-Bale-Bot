"""The five scored questions."""

import asyncio

from bot_instance import bot
from data.content import QUESTIONS
from database.db import get_user, update_user
from handlers.states import STATE_QUIZ
from keyboards.builders import choice_keyboard
from utils.helpers import to_persian_digits


LABELS = ["الف", "ب", "ج", "د", "ه"]


async def start_quiz(user_id):
    await update_user(user_id, state=STATE_QUIZ, step=0, answers=[])
    await send_question(user_id, 0)


async def send_question(user_id, index):
    question = QUESTIONS[index]
    options = question["options"]
    options_text = "\n".join(f"{LABELS[i]}) {opt['text']}" for i, opt in enumerate(options))
    header = f"سؤال {to_persian_digits(index + 1)} از {to_persian_digits(len(QUESTIONS))}\n\n"
    full_text = header + question["text"] + "\n\n" + options_text + "\n\n👇 یک گزینه را انتخاب کنید:"
    labels = LABELS[:len(options)]
    await bot.send_message(
        user_id,
        text=full_text,
        reply_markup=choice_keyboard("quiz", index, labels)
    )


async def handle_quiz_answer(user_id, index, option_index):
    """Record one answer. Out-of-turn taps (old messages) are rejected."""
    user = await get_user(user_id)
    if user is None or index != user["step"]:
        return False
    options = QUESTIONS[index]["options"]
    if not 0 <= option_index < len(options):
        return False

    answers = list(user["answers"])
    answers.append(options[option_index]["code"])
    next_step = index + 1
    await update_user(user_id, answers=answers, step=next_step)

    # ارسال پیام تأیید قبل از سوال بعدی
    await bot.send_message(user_id, "✅ پاسخ شما ثبت شد.")
    # مکث کوتاه (اختیاری) برای اطمینان از نمایش پیام تأیید
    await asyncio.sleep(0.3)

    if next_step < len(QUESTIONS):
        await send_question(user_id, next_step)
    else:
        from handlers.result import send_result
        await send_result(user_id)
    return True