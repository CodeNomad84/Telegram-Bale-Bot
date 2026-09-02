import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot_instance import bot
from database.db import get_all_user_ids

async def send_daily_messages():
    """ارسال پیام‌های روزانه به همه کاربران"""
    user_ids = await get_all_user_ids()
    messages = [
        "سلام یارحسین✋🏼\nاوضاع و احوال زندگی چطوره؟\nخانواده خوبن؟",
        "بیا یه کار هیجان‌انگیز انجام بدیم🫢\nآماده یه مأموریت هستی؟",
        "مجردی؟ دوست داری بدونی در آینده سبک تعاملت با فرزندت چجوریه؟🤓\nمتأهلی؟ میدونی با چه سبکی داری فرزندت رو بزرگ می‌کنی؟🤔",
        "بیا این بازی رو انجام بده تا بهت بگم شخصیت والدگری تو چه شکلیه! 😁"
    ]
    
    for user_id in user_ids:
        for msg in messages:
            try:
                await bot.send_message(user_id, msg)
                await asyncio.sleep(0.5)  # جلوگیری از محدودیت نرخ
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")
        # فاصله بین ارسال سریال پیام‌ها برای هر کاربر
        await asyncio.sleep(1)

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