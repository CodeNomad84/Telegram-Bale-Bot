"""Admin panel entry point, callback router, and text handler for admin actions."""

from balethon.objects import InlineKeyboard

from bot_instance import bot
from config import ADMIN_IDS
from database.db import log_admin_action
from keyboards.builders import (
    admin_main_keyboard,
    admin_back_keyboard,
    admin_cancel_keyboard,
    prize_menu_keyboard,
    lottery_type_keyboard,
    lottery_count_keyboard,
    prize_category_keyboard,
)

from admin.stats import get_stats_text
from admin.broadcast import broadcast_send
from admin.export import export_users_excel
from admin.graph import generate_graph
from admin.prize import (
    DEFAULT_COUNTS,
    CATEGORY_NAMES,
    run_lottery,
    format_winners_list,
    send_prize_message,
)
from admin.logs import get_logs_text
from utils.decorators import admin_message_required, admin_required
from utils.helpers import safe_answer

# ذخیره‌سازی موقت وضعیت ادمین
ADMIN_STATE = {}
# ذخیره‌سازی نتایج قرعه‌کشی هر ادمین برای استفاده در ارسال جایزه
ADMIN_LOTTERY_RESULTS = {}  # {admin_id: {category: [user_ids]}}


async def show_admin_panel(user_id):
    await bot.send_message(
        user_id,
        "🔐 پنل مدیریت\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_main_keyboard()
    )


async def _show_prize_menu(user_id):
    """نمایش منوی جوایز."""
    await bot.send_message(
        user_id,
        "🎁 بخش جوایز\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=prize_menu_keyboard()
    )


@admin_required
async def admin_callback(callback_query):
    user_id = callback_query.author.id
    data = callback_query.data

    # ---------- اصلی ----------
    if data == "admin:main":
        await safe_answer(callback_query, "")
        await show_admin_panel(user_id)
        return

    if data == "admin:cancel":
        ADMIN_STATE.pop(user_id, None)
        await safe_answer(callback_query, "عملیات لغو شد.")
        await show_admin_panel(user_id)
        return

    # ---------- آمار ----------
    if data == "admin:stats":
        await safe_answer(callback_query, "")
        text = await get_stats_text()
        await bot.send_message(user_id, text, reply_markup=admin_back_keyboard())
        return

    # ---------- ارسال پیام همگانی ----------
    if data == "admin:broadcast":
        await safe_answer(callback_query, "لطفاً پیام خود را ارسال کنید.")
        ADMIN_STATE[user_id] = {"action": "broadcast"}
        await bot.send_message(
            user_id,
            "✏️ پیام خود را بنویسید. پس از ارسال، از شما تأیید می‌گیرم.",
            reply_markup=admin_cancel_keyboard()
        )
        return

    if data == "admin:broadcast_confirm":
        state = ADMIN_STATE.get(user_id)
        if not state or state.get("action") != "broadcast":
            await safe_answer(callback_query, "هیچ پیامی برای تأیید وجود ندارد.")
            return
        text = state.get("broadcast_text")
        if not text:
            await safe_answer(callback_query, "متن پیام خالی است.")
            return
        await safe_answer(callback_query, "در حال ارسال...")
        sent, failed = await broadcast_send(user_id, text)
        await bot.send_message(
            user_id,
            f"✅ ارسال کامل شد.\nموفق: {sent}\nناموفق: {failed}"
        )
        ADMIN_STATE.pop(user_id, None)
        await show_admin_panel(user_id)
        return

    # ---------- خروجی اکسل ----------
    if data == "admin:export":
        await safe_answer(callback_query, "در حال تولید فایل اکسل...")
        file_path = await export_users_excel()
        with open(file_path, "rb") as f:
            await bot.send_document(
                user_id,
                document=f,
                caption="📊 خروجی کامل کاربران و دعوت‌کنندگان"
            )
        await log_admin_action(user_id, "export_excel", f"file: {file_path}")
        return

    # ---------- نمودار ----------
    if data == "admin:graph":
        await safe_answer(callback_query, "در حال تولید نمودار...")
        img_path = await generate_graph()
        with open(img_path, "rb") as f:
            await bot.send_photo(
                user_id,
                photo=f,
                caption="📈 شبکه دعوت‌کنندگان و دعوت‌شدگان"
            )
        return

    # ---------- منوی جوایز ----------
    if data == "admin:prize":
        await safe_answer(callback_query, "")
        await _show_prize_menu(user_id)
        return

    # ---------- قرعه‌کشی: انتخاب نوع ----------
    if data == "admin:lottery":
        await safe_answer(callback_query, "")
        await bot.send_message(
            user_id,
            "🎲 نوع قرعه‌کشی را انتخاب کنید:",
            reply_markup=lottery_type_keyboard()
        )
        return

    # ---------- قرعه‌کشی: انتخاب دسته ----------
    if data.startswith("admin:lottery:"):
        await safe_answer(callback_query, "")
        category = data.split(":")[2]
        default_count = DEFAULT_COUNTS.get(category, 5)
        ADMIN_STATE[user_id] = {
            "action": "lottery_count",
            "category": category,
            "default_count": default_count,
        }
        await bot.send_message(
            user_id,
            f"🔢 چند نفر انتخاب شوند؟\n"
            f"پیش‌فرض: {default_count} نفر\n\n"
            f"یک عدد بفرستید یا از دکمهٔ زیر برای استفاده از پیش‌فرض استفاده کنید.",
            reply_markup=lottery_count_keyboard()
        )
        return

    # ---------- قرعه‌کشی: استفاده از پیش‌فرض ----------
    if data == "admin:lottery_use_default":
        state = ADMIN_STATE.get(user_id)
        if not state or state.get("action") != "lottery_count":
            await safe_answer(callback_query, "ابتدا یک دسته انتخاب کنید.")
            return
        await safe_answer(callback_query, "در حال اجرای قرعه‌کشی...")
        category = state["category"]
        count = state["default_count"]
        await _perform_lottery(user_id, category, count)
        return

    # ---------- ارسال پیام جایزه: انتخاب دسته ----------
    if data == "admin:prize_message":
        await safe_answer(callback_query, "")
        await bot.send_message(
            user_id,
            "📨 پیام جایزه برای کدام دسته ارسال شود؟",
            reply_markup=prize_category_keyboard()
        )
        return

    # ---------- ارسال پیام جایزه: دریافت دسته ----------
    if data.startswith("admin:prize_cat:"):
        await safe_answer(callback_query, "")
        category = data.split(":")[2]
        # بررسی وجود نتیجه قرعه‌کشی قبلی برای این دسته
        admin_results = ADMIN_LOTTERY_RESULTS.get(user_id, {})
        if category in admin_results and admin_results[category]:
            winners = admin_results[category]
            # ذخیره برندگان در state و پرسیدن پیام
            ADMIN_STATE[user_id] = {
                "action": "prize_message_text",
                "category": category,
                "winners": winners,
            }
            await bot.send_message(
                user_id,
                f"👥 برندگان انتخابی: {len(winners)} نفر\n\n"
                f"📝 لطفاً پیام جایزه را بنویسید:",
                reply_markup=admin_cancel_keyboard()
            )
        else:
            # اگر قرعه‌کشی قبلی نبود، با مقدار پیش‌فرض اجرا کن
            default_count = DEFAULT_COUNTS.get(category, 5)
            winners = await run_lottery(category, default_count)
            if not winners:
                await bot.send_message(user_id, "⚠️ هیچ کاربری برای این دسته یافت نشد.")
                ADMIN_STATE.pop(user_id, None)
                return
            ADMIN_STATE[user_id] = {
                "action": "prize_message_text",
                "category": category,
                "winners": winners,
            }
            await bot.send_message(
                user_id,
                f"👥 {len(winners)} نفر به‌صورت خودکار انتخاب شدند "
                f"(قرعه‌کشی با پیش‌فرض).\n\n"
                f"📝 لطفاً پیام جایزه را بنویسید:",
                reply_markup=admin_cancel_keyboard()
            )
        return

    # ---------- لاگ‌ها ----------
    if data == "admin:logs":
        await safe_answer(callback_query, "")
        text = await get_logs_text()
        await bot.send_message(user_id, text, reply_markup=admin_back_keyboard())
        return

    await safe_answer(callback_query, "دستور ناشناخته")


async def _perform_lottery(user_id, category, count):
    """اجرای قرعه‌کشی و نمایش نتیجه."""
    winners = await run_lottery(category, count)
    if not winners:
        await bot.send_message(user_id, "⚠️ هیچ کاربری برای این دسته یافت نشد.")
        ADMIN_STATE.pop(user_id, None)
        return

    # ذخیره نتایج برای استفاده در ارسال پیام جایزه
    ADMIN_LOTTERY_RESULTS.setdefault(user_id, {})[category] = winners

    # نمایش برندگان
    text = await format_winners_list(winners, category)
    await bot.send_message(
        user_id,
        text + "\n\n✅ برای ارسال پیام جایزه، از منوی «ارسال پیام جایزه» استفاده کنید.",
        reply_markup=admin_back_keyboard()
    )
    ADMIN_STATE.pop(user_id, None)
    await log_admin_action(user_id, "lottery", f"category: {category}, count: {len(winners)}")


@admin_message_required
async def admin_message(message):
    """پردازش پیام‌های متنی ادمین در حالت‌های ویژه."""
    user_id = message.author.id
    if user_id not in ADMIN_STATE:
        return

    state = ADMIN_STATE[user_id]
    action = state.get("action")

    # ---------- پیام همگانی ----------
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

    # ---------- تعداد قرعه‌کشی ----------
    if action == "lottery_count":
        text = (message.text or "").strip()
        # تبدیل اعداد فارسی
        persian_digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        text = text.translate(persian_digits)

        if text == "" or text == ".":
            # استفاده از پیش‌فرض
            count = state["default_count"]
        else:
            try:
                count = int(text)
                if count <= 0:
                    raise ValueError
            except ValueError:
                await bot.send_message(
                    user_id,
                    "⚠️ لطفاً یک عدد مثبت وارد کنید یا از دکمهٔ پیش‌فرض استفاده کنید."
                )
                return

        category = state["category"]
        await _perform_lottery(user_id, category, count)
        return

        # ---------- پیام جایزه ----------
    if action == "prize_message_text":
        text = (message.text or "").strip()
        if not text:
            await bot.send_message(user_id, "پیام نمی‌تواند خالی باشد.")
            return
        winners = state.get("winners", [])
        category = state.get("category", "")
        if not winners:
            await bot.send_message(user_id, "⚠️ لیست برندگان خالی است.")
            ADMIN_STATE.pop(user_id, None)
            return

        await bot.send_message(user_id, "در حال ارسال جایزه...")
        sent, failed = await send_prize_message(user_id, winners, text, category)
        await bot.send_message(
            user_id,
            f"✅ پیام جایزه ارسال شد.\n"
            f"دسته: {CATEGORY_NAMES.get(category, category)}\n"
            f"موفق: {sent}\nناموفق: {failed}\n\n"
            f"ℹ️ برندگان می‌توانند اطلاعات خود را برای شما ارسال کنند.",
            reply_markup=admin_back_keyboard()
        )
        ADMIN_STATE.pop(user_id, None)
        return