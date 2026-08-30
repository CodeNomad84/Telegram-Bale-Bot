"""Admin panel entry point, callback router, and text handler for admin actions."""

from balethon.objects import InlineKeyboard

from bot_instance import bot
from config import ADMIN_IDS
from database.db import log_admin_action
from keyboards.builders import admin_main_keyboard, admin_back_keyboard, admin_cancel_keyboard
from admin.stats import get_stats_text
from admin.broadcast import broadcast_send
from admin.export import export_users_excel
from admin.graph import generate_graph
from admin.prize import prize_send
from admin.logs import get_logs_text
from utils.decorators import admin_required

# Admin state dictionary: stores temporary data for each admin user
ADMIN_STATE = {}


async def show_admin_panel(user_id):
    await bot.send_message(
        user_id,
        "🔐 پنل مدیریت\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_main_keyboard()
    )


@admin_required
async def admin_callback(callback_query):
    user_id = callback_query.author.id
    data = callback_query.data

    if data == "admin:main":
        await show_admin_panel(user_id)
        return

    if data == "admin:cancel":
        ADMIN_STATE.pop(user_id, None)
        await bot.send_message(user_id, "❌ عملیات لغو شد.")
        await show_admin_panel(user_id)
        return

    if data == "admin:stats":
        text = await get_stats_text()
        await bot.send_message(user_id, text, reply_markup=admin_back_keyboard())
        return

    if data == "admin:broadcast":
        ADMIN_STATE[user_id] = {"action": "broadcast"}
        await bot.send_message(
            user_id,
            "✏️ لطفاً پیام خود را ارسال کنید (فقط متن).\nپس از ارسال، از شما تأیید می‌گیرم.",
            reply_markup=admin_cancel_keyboard()
        )
        return

    if data == "admin:export":
        # ارسال پیام برای مطلع کردن ادمین از شروع فرآیند پردازش سنگین
        status_msg = await bot.send_message(user_id, "🔄 در حال تولید فایل اکسل، لطفاً شکیبا باشید...")
        
        file_path = await export_users_excel()
        with open(file_path, "rb") as f:
            await bot.send_document(user_id, document=f, caption="📊 خروجی کامل کاربران")
        await log_admin_action(user_id, "export_excel", f"file: {file_path}")
        return

    if data == "admin:graph":
        # اطلاع‌رسانی فرآیند رسم نمودار
        status_msg = await bot.send_message(user_id, "📊 در حال تولید و رسم نمودار...")
        
        img_path = await generate_graph()
        with open(img_path, "rb") as f:
            await bot.send_photo(user_id, photo=f, caption="📈 شبکه دعوت‌کنندگان و دعوت‌شدگان")
        return

    if data == "admin:prize":
        ADMIN_STATE[user_id] = {"action": "prize"}
        await bot.send_message(
            user_id,
            "🔍 لطفاً معیارهای انتخاب برندگان را مشخص کنید.\nمعیارها را به‌صورت `result_code=1` یا `invites>=5` وارد کنید.",
            reply_markup=admin_cancel_keyboard()
        )
        return

    if data == "admin:logs":
        text = await get_logs_text()
        await bot.send_message(user_id, text, reply_markup=admin_back_keyboard())
        return

    # Broadcast confirmation
    if data == "admin:broadcast_confirm":
        state = ADMIN_STATE.get(user_id)
        if not state or state.get("action") != "broadcast":
            await bot.send_message(user_id, "⚠️ هیچ پیامی برای تأیید وجود ندارد.")
            return
        text = state.get("broadcast_text")
        if not text:
            await bot.send_message(user_id, "⚠️ متن پیام خالی است.")
            return
            
        await bot.send_message(user_id, "🔄 در حال ارسال پیام همگانی به کاربران...")
        sent, failed = await broadcast_send(user_id, text)
        await bot.send_message(
            user_id,
            f"✅ ارسال کامل شد.\nارسال به {sent} کاربر موفق، {failed} کاربر ناموفق."
        )
        ADMIN_STATE.pop(user_id, None)
        await show_admin_panel(user_id)
        return

    await bot.send_message(user_id, "دستور ناشناخته")


@admin_required
async def admin_message(message):
    # کدهای این بخش بدون تغییر باقی می‌مانند...
    user_id = message.author.id
    if user_id not in ADMIN_STATE:
        return

    state = ADMIN_STATE[user_id]
    action = state.get("action")

    if action == "broadcast":
        text = message.text
        if not text:
            await bot.send_message(user_id, "لطفاً یک پیام متنی ارسال کنید.")
            return
        ADMIN_STATE[user_id]["broadcast_text"] = text
        await bot.send_message(
            user_id,
            f"📨 پیام زیر به همه کاربران ارسال شود؟\n\n{text}",
            reply_markup=InlineKeyboard(
                [{"text": "✅ بله، ارسال کن", "callback_data": "admin:broadcast_confirm"}],
                [{"text": "❌ خیر، لغو", "callback_data": "admin:cancel"}]
            )
        )
        return

    if action == "prize":
        criteria = message.text
        ADMIN_STATE[user_id]["prize_criteria"] = criteria
        ADMIN_STATE[user_id]["action"] = "prize_message"
        await bot.send_message(
            user_id,
            "📝 حالا پیام جایزه را بنویسید.",
            reply_markup=admin_cancel_keyboard()
        )
        return

    if action == "prize_message":
        criteria = state.get("prize_criteria")
        prize_msg = message.text
        if not criteria or not prize_msg:
            await bot.send_message(user_id, "معیار یا پیام جایزه کامل نیست. دوباره تلاش کنید.")
            return
        await bot.send_message(user_id, "در حال ارسال جوایز...")
        await prize_send(user_id, criteria, prize_msg)
        ADMIN_STATE.pop(user_id, None)
        await show_admin_panel(user_id)
        return
