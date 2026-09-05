"""Central configuration: paths, credentials and campaign copy."""

import os, dotenv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# ---------- Connection ----------
TOKEN = dotenv.get_key(dotenv.find_dotenv(), "BALE_TOKEN")
# # BOT_USERNAME = os.getenv("BOT_USERNAME", "@keramat_bot")
# CHANNEL_ID = os.getenv("CHANNEL_ID", "@keraamat")
# CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://ble.ir/join/EctQtirbPs")
# BOT_USERNAME = os.getenv("BOT_USERNAME", "@keramat_bot")
# ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x}
BOT_USERNAME = dotenv.get_key(dotenv.find_dotenv(),"BOT_USERNAME")
CHANNEL_ID = dotenv.get_key(dotenv.find_dotenv(), "CHANNEL_ID")
CHANNEL_LINK = dotenv.get_key(dotenv.find_dotenv(), "CHANNEL_LINK")
ADMIN_IDS = {int(x) for x in dotenv.get_key(dotenv.find_dotenv(), "ADMIN_IDS").replace(" ", "").split(",") if x}

# ---------- Paths ----------
DATA_DIR = BASE_DIR / "data"
PICS_DIR = BASE_DIR / "pics"
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "keramat.db"
DOCX_PATH = BASE_DIR / "bot_def.docx"

INTRO_FILE = DATA_DIR / "INTRO.xlsx"
QUESTIONS_FILE = DATA_DIR / "QUESTIONS.xlsx"
RESULT_TEXTS_FILE = DATA_DIR / "RESULT_TEXTS.xlsx"
RESULT_IMAGES_FILE = DATA_DIR / "RESULT_IMAGES.xlsx"
PRODUCTS_FILE = DATA_DIR / "PRODUCTS.xlsx"
INVITE_IMAGE = PICS_DIR / "invite.jpg"

# ---------- Logging ----------
LOG_FILE = BASE_DIR / "admin_logs.txt"   # fallback if DB logging fails

# ---------- Campaign copy ----------
CAMPAIGN_TITLE = "ربات مرحله دو تربیت فرزند، تربیت بدون اشک"
CAMPAIGN_HEADLINE = "*مجرد  یا متاهل فرقی نداره* ، بیاید بهتون بگیم سبک تربیتی شما چیه!"
WELCOME_TEXT = (
    f"{CAMPAIGN_HEADLINE}!\n\n"
    f"به «{CAMPAIGN_TITLE}» خوش آمدید 😊.\n"
    "قراره در چند سؤال کوتاه سبک تربیتی رو پیدا کنیم.\n"
    "فرقی نمی‌کنه مجرد باشی یا متأهل، مادر باشی یا پدر.\n\n"
    "*💢 البته هیچ چیز قطعی نیست!*\n\n"
    "برای شروع، اول عضو کانال شو و بعد دکمهٔ «بررسی عضویت» را بزن 👇"
)

NOT_JOINED_TEXT = "هنوز عضو کانال نشدی! اول عضو شو، بعد دوباره «بررسی عضویت» را بزن."

ASK_USERNAME_TEXT = (
    "اگر دوست داشتی، آیدی بله‌ات را بفرست (با @ شروع می‌شود؛ مثل @meysam).\n"
    "این کار اختیاری است و فقط برای اطلاع‌رسانی قرعه‌کشی و پیام‌های اختصاصی به کار می‌رود.\n"
    "اگر نمی‌خواهی، دکمهٔ زیر را بزن؛ آزمون بدون آن هم کامل انجام می‌شود."
)

INVALID_USERNAME_TEXT = (
    "آیدی باید با @ شروع شود و فقط شامل حرف انگلیسی، عدد و _ باشد (حداقل ۴ نویسه).\n"
    "دوباره بفرست یا از دکمهٔ رد کردن استفاده کن."
)

ASK_PHONE_TEXT = (
    "در صورت تمایل جهت اطلاع از اخبار و آشنایی با دوره‌های مجموعه *کرامت*، شماره تماس خودتون رو وارد کنید\n"
    "در صورت عدم‌تمایل، می‌توانید از دکمهٔ «رد کردن» استفاده کنید."
)

FALLBACK_TEXT = "برای ادامه از دکمه‌های همان پیام استفاده کن، یا با /start از نو شروع کن 🙂"
NO_ANSWERS_TEXT = "پاسخی ثبت نشده. با /start دوباره شروع کن."