"""Routing only: messages and callback queries are dispatched to handlers."""

import asyncio
import traceback

from bot_instance import bot
from config import ADMIN_IDS, CHANNEL_ID, FALLBACK_TEXT, NOT_JOINED_TEXT
from database.db import ensure_user, get_user, init_db, register_invite, reset_quiz
from handlers.intro import handle_intro_answer
from handlers.membership import is_member
from handlers.quiz import handle_quiz_answer
from handlers.registration import (
    # ask_username,
    handle_phone_text,
    handle_username_text,
    send_welcome_gate,
    ask_phone,
    skip_phone,
    # skip_username,
    greet_and_start
)
from handlers.states import STATE_AWAIT_PHONE, build_display_name #, STATE_AWAIT_USERNAME

# Import admin handlers
from admin.handlers import ADMIN_STATE, admin_callback, admin_message, show_admin_panel

# Inviter ids held between /start and a confirmed channel membership.
PENDING_INVITER = {}


def parse_start_payload(text):
    """Extract the inviter id from "/start <user_id>", if present."""
    parts = (text or "").split(maxsplit=1)
    if len(parts) == 2 and parts[1].strip().isdigit():
        return int(parts[1].strip())
    return None


@bot.on_message()
async def on_message(message):
    """Main message handler with debug logs."""
    try:
        # ۱. بررسی حیاتی: اگر پیام نویسنده ندارد (پیام سیستمی یا کانال) یا چت خصوصی نیست، فوراً متوقف کن
        if message.author is None or message.chat is None:
            return
            
        # همچنین مطمئن می‌شویم پیام از یک کانال فوروارد یا ارسال نشده باشد
        if message.chat.type != "private":
            return

        user_id = message.author.id
        text = (message.text or "").strip()

        # چاپ لاگ فقط پس از اطمینان از وجود کاربر
        print(f"[DEBUG] Received message from {user_id}: {text}")
        print(f"[DEBUG] user_id={user_id}, text='{text}'")

        # Ensure user exists
        await ensure_user(user_id, build_display_name(message.author))
        print("[DEBUG] ensure_user done.")

        # ---------- Admin command ----------
        if text == "/admin":
            print("[DEBUG] /admin command received.")
            if user_id not in ADMIN_IDS:
                await bot.send_message(user_id, "⛔ شما دسترسی ادمین ندارید.")
                print("[DEBUG] Not admin.")
                return
            await show_admin_panel(user_id)
            print("[DEBUG] Admin panel shown.")
            return

        # ---------- Admin text handling ----------
        if user_id in ADMIN_IDS and user_id in ADMIN_STATE:
            print("[DEBUG] Admin state active, forwarding to admin_message.")
            await admin_message(message)
            return

        # ---------- /start ----------
        if text.startswith("/start"):
            print("[DEBUG] /start command received.")
            inviter_id = parse_start_payload(text)
            if inviter_id and inviter_id != user_id:
                PENDING_INVITER[user_id] = inviter_id
                print(f"[DEBUG] Pending inviter set: {inviter_id}")
            await reset_quiz(user_id)
            await send_welcome_gate(user_id)
            print("[DEBUG] Welcome gate sent.")
            return

        # ---------- Stateful handlers ----------
        user = await get_user(user_id)
        print(f"[DEBUG] User state: {user['state'] if user else 'None'}")
        # if user and user["state"] == STATE_AWAIT_USERNAME:
        #     print("[DEBUG] Awaiting username, forwarding.")
        #     await handle_username_text(user_id, text)
        #     return
        if user and user["state"] == STATE_AWAIT_PHONE:
            print("[DEBUG] Awaiting phone, forwarding.")
            await handle_phone_text(user_id, text)
            return

        # Any other free‑text message: point the user back to the buttons.
        print("[DEBUG] No state match, sending fallback.")
        await bot.send_message(user_id, text=FALLBACK_TEXT)

    except Exception as e:
        print(f"[ERROR] in on_message: {e}")
        traceback.print_exc()
        # ارسال پیام خطا فقط در صورتی که شناسه کاربر واقعاً معتبر و بالای صفر باشد
        if 'user_id' in locals() and user_id > 0:
            try:
                await bot.send_message(user_id, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")
            except:
                pass


@bot.on_callback_query()
async def on_callback_query(callback_query):
    """Main callback handler with debug logs."""
    try:
        print(f"[DEBUG] Received callback: {callback_query.data} from {callback_query.author.id}")
        if callback_query.author is None:
            print("[DEBUG] No author, ignoring.")
            return
        user_id = callback_query.author.id
        data = callback_query.data

        # ---------- Admin callbacks ----------
        if data.startswith("admin:"):
            print("[DEBUG] Admin callback.")
            # پاسخ سریع با متن خالی (اجباری)
            await callback_query.answer("")
            await admin_callback(callback_query)
            return

        # ---------- Check membership ----------
        if data == "check_join":
            print("[DEBUG] check_join callback.")
            if not await is_member(user_id):
                await callback_query.answer(NOT_JOINED_TEXT, show_alert=True)
                print("[DEBUG] Not member.")
                return
            # عضو است
            await callback_query.answer("عضویتت تأیید شد ✅")
            inviter_id = PENDING_INVITER.pop(user_id, None)
            if inviter_id:
                await register_invite(inviter_id, user_id)
                print(f"[DEBUG] Registered invite from {inviter_id}")
            # await ask_username(user_id)
            await ask_phone(user_id)
            return

        # ---------- Skip username ----------
        # if data == "username:skip":
        #     print("[DEBUG] Skip username.")
        #     await callback_query.answer("باشه، بدون آیدی ادامه می‌دهیم")
        #     await skip_username(user_id)
        #     return

        # ---------- Skip phone ----------
        if data == "phone:skip":
            print("[DEBUG] Skip phone.")
            await callback_query.answer("شماره تماس ذخیره نشد")
            await skip_phone(user_id)
            return

        # ---------- Restart ----------
        if data == "restart":
            print("[DEBUG] Restart.")
            await callback_query.answer("از نو شروع می‌کنیم 🔄")
            await reset_quiz(user_id)
            await send_welcome_gate(user_id)
            return

        # ---------- Intro & Quiz answers ----------
        if data.startswith("intro:") or data.startswith("quiz:"):
            print(f"[DEBUG] {data} answer.")
            try:
                kind, index, option_index = data.split(":")
                index, option_index = int(index), int(option_index)
            except ValueError:
                await callback_query.answer("دادهٔ نامعتبر")
                return

            # پاسخ اولیه (نوتیفیکیشن)
            await callback_query.answer("در حال ثبت پاسخ...")

            # پردازش پاسخ (بدون ارسال پیام تأیید در اینجا)
            handler = handle_intro_answer if kind == "intro" else handle_quiz_answer
            await handler(user_id, index, option_index)
            # دیگر پیام "✅ پاسخ شما ثبت شد." اینجا ارسال نمی‌شود
            return

        # Fallback: پاسخ به هر callback ناشناخته
        print("[DEBUG] Unknown callback, answering.")
        await callback_query.answer("")

    except Exception as e:
        print(f"[ERROR] in on_callback_query: {e}")
        traceback.print_exc()
        try:
            await callback_query.answer("خطا در پردازش درخواست", show_alert=True)
        except:
            pass


async def startup():
    print("[DEBUG] Initializing database...")
    await init_db()
    print("[DEBUG] Database initialized.")
    start_scheduler()

    # تست دسترسی به کانال (اختیاری)
    if CHANNEL_ID:
        try:
            chat = await bot.get_chat(CHANNEL_ID)
            print(f"[DEBUG] Channel found: {chat.title} (id: {chat.id})")
        except Exception as e:
            print(f"[ERROR] Cannot access channel: {e}")
            print("[WARNING] Membership check may fail. Check CHANNEL_ID in config.")
    else:
        print("[DEBUG] No channel ID set, membership check disabled.")


if __name__ == "__main__":
    print("[DEBUG] Starting bot...")
    asyncio.get_event_loop().run_until_complete(startup())
    print("[DEBUG] Running bot...")
    bot.run()