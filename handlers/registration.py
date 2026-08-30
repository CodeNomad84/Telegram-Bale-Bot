"""Welcome gate, username, and phone number steps."""

from bot_instance import bot
from config import ASK_PHONE_TEXT, ASK_USERNAME_TEXT, INVALID_USERNAME_TEXT, WELCOME_TEXT
from database.db import get_user, update_user
from handlers.intro import start_intro
from handlers.states import (
    STATE_AWAIT_JOIN,
    STATE_AWAIT_PHONE,
    STATE_AWAIT_USERNAME,
    address_of,
    normalize_username,
)
from keyboards.builders import join_keyboard, phone_keyboard, username_keyboard


async def send_welcome_gate(user_id):
    """Send the campaign intro with join + membership check buttons."""
    await update_user(user_id, state=STATE_AWAIT_JOIN)
    await bot.send_message(user_id, text=WELCOME_TEXT, reply_markup=join_keyboard())


# async def ask_username(user_id):
#     """Ask for the @username; skipping is always allowed."""
#     await update_user(user_id, state=STATE_AWAIT_USERNAME)
#     await bot.send_message(user_id, text=ASK_USERNAME_TEXT, reply_markup=username_keyboard())


async def handle_username_text(user_id, text):
    """Validate and store the username, then continue to phone step."""
    username = normalize_username(text)
    if username is None:
        await bot.send_message(
            user_id, text=INVALID_USERNAME_TEXT, reply_markup=username_keyboard()
        )
        return
    await update_user(user_id, username=username)
    await ask_phone(user_id)


# async def skip_username(user_id):
#     """Continue without a username."""
#     await ask_phone(user_id)


async def ask_phone(user_id):
    """Ask for phone number (optional)."""
    await update_user(user_id, state=STATE_AWAIT_PHONE)
    await bot.send_message(user_id, text=ASK_PHONE_TEXT, reply_markup=phone_keyboard())


async def handle_phone_text(user_id, text):
    """Store the phone number (any text is accepted) and continue."""
    await update_user(user_id, phone=text.strip())
    await greet_and_start(user_id)


async def skip_phone(user_id):
    """Continue without phone number."""
    await update_user(user_id, phone=None)
    await greet_and_start(user_id)


async def greet_and_start(user_id):
    """Greet with "[name] خوش آمدی!" and enter the intro flow."""
    user = await get_user(user_id)
    await bot.send_message(user_id, text=f"{address_of(user)} خوش آمدی! 🌸")
    await start_intro(user_id)