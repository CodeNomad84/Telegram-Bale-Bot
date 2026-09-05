import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot_instance import bot
from database.db import get_all_user_ids

# لیست پیام‌ها (ترتیب مهم است)
MESSAGES = [
    "سلام یارحسین✋🏼\nاوضاع و احوال زندگی چطوره؟\nخانواده خوبن؟",
    "بیا یه کار هیجان‌انگیز انجام بدیم🫢\nآماده یه مأموریت هستی؟",
    "مجردی؟ دوست داری بدونی در آینده سبک تعاملت با فرزندت چجوریه؟🤓\nمتأهلی؟ میدونی با چه سبکی داری فرزندت رو بزرگ می‌کنی؟🤔",
    "بیا این بازی رو انجام بده تا بهت بگم شخصیت والدگری تو چه شکلیه! 😁"
]

# فایل برای ذخیره آخرین اندیس ارسال‌شده
STATE_FILE = "scheduler_state.txt"


def get_next_message():
    """
    اندیس فعلی را از فایل می‌خواند، پیام متناظر را برمی‌گرداند
    و سپس اندیس را برای دفعه بعد افزایش می‌دهد.
    """
    index = 0
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                index = int(f.read().strip())
            except ValueError:
                index = 0

    # انتخاب پیام بر اساس اندیس فعلی
    message = MESSAGES[index % len(MESSAGES)]

    # افزایش اندیس و ذخیره برای دفعه بعد
    next_index = (index + 1) % len(MESSAGES)
    with open(STATE_FILE, "w") as f:
        f.write(str(next_index))

    return message


async def send_daily_messages():
    """ارسال یک پیام روزانه به همه کاربران (چرخشی)"""
    user_ids = await get_all_user_ids()
    if not user_ids:
        print("[Scheduler] No users to send messages.")
        return

    msg = get_next_message()
    print(f"[Scheduler] Sending message to {len(user_ids)} users: {msg[:30]}...")

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, msg)
            await asyncio.sleep(0.5)  # جلوگیری از محدودیت نرخ
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")


def start_scheduler():
    scheduler = AsyncIOScheduler()
    # زمان‌بندی هر شب ساعت ۲۳:۰۰ به وقت سرور
    scheduler.add_job(
        send_daily_messages,
        trigger=CronTrigger(hour=23, minute=0),
        id="daily_messages"
    )
    scheduler.start()
    print("[Scheduler] Daily messages scheduled for 23:00")