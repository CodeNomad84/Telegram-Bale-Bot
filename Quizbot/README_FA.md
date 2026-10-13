# والد‌یار (Valedyar)

## الف) معرفی

ربات **والد‌یار** یک آزمون کوتاه برای شناسایی **سبک تربیتی والدگری** است که روی پیام‌رسان **بله** اجرا می‌شود.

- **مخاطب:** والدین، مجردها و متأهل‌ها. مجردها سبک تعامل آینده‌شان با فرزند را می‌بینند و والدین سبک فعلی‌شان را.
- **پلتفرم:** پیام‌رسان بله
- **کتابخانه:** [`balethon`](https://pypi.org/project/balethon/)

### روند کار کاربر

1. بررسی عضویت اجباری در کانال
2. دریافت شماره تماس (اختیاری)
3. سؤالات مقدماتی: وضعیت تأهل، و برای والدین جنسیت فرزند
4. پرسشنامهٔ ۵ سؤالی
5. نمایش نتیجه: یکی از ۵ تیپ تربیتی، با تصویر متناسب با جنسیت
6. پیشنهاد دوره بر اساس پاسخ‌های مقدماتی
7. لینک دعوت اختصاصی برای شرکت در قرعه‌کشی

---

## ب) پیش‌نیازها

- پایتون **۳.۱۰** یا بالاتر
- `pip` و `venv`
- دسترسی SSH به سرور (برای استقرار)
- توکن ربات از `@BotFather` در بله
- **ربات باید ادمین کانال باشد.** بدون این دسترسی، بررسی عضویت کار نمی‌کند و همهٔ کاربران «غیرعضو» دیده می‌شوند.

---

## ج) نصب و راه‌اندازی محلی

```bash
git clone https://github.com/CodeNomad84/Telegram-Bale-Bot.git
cd Telegram-Bale-Bot/Quizbot
python3 -m venv venv
source venv/bin/activate        # در ویندوز: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.local.example .env   # در ویندوز: copy ..\.env.local.example .env
# فایل .env را ویرایش کنید و مقادیر واقعی را قرار دهید
python verify.py                # تست آفلاین
python main.py
```

> فایل `.env.local.example` در **ریشهٔ مخزن** است. فایل `.env` می‌تواند در پوشهٔ `Quizbot/` یا در ریشهٔ مخزن باشد. برنامه از پوشهٔ `Quizbot/` به بالا دنبال آن می‌گردد و اولین فایلی را که پیدا کند استفاده می‌کند.

### متغیرهای `.env`

| متغیر | توضیح | نمونه |
|---|---|---|
| `BALE_TOKEN` | توکن ربات از BotFather | `123456789:abc...` |
| `BOT_USERNAME` | نام کاربری ربات (برای ساخت لینک دعوت) | `@your_bot` |
| `CHANNEL_ID` | کانال عضویت اجباری. اگر خالی باشد، بررسی عضویت انجام نمی‌شود | `@your_channel` |
| `CHANNEL_LINK` | لینک عضویت کانال برای دکمهٔ «عضویت» | `https://ble.ir/join/...` |
| `ADMIN_IDS` | شناسهٔ عددی ادمین‌ها، جداشده با کاما | `111111111,222222222` |

---

## د) استقرار روی سرور (systemd)

| مورد | مقدار |
|---|---|
| نام سرویس | `keramat-bot.service` |
| مسیر پروژه | `/home/ubuntu/Telegram-Bale-Bot/Quizbot` |

### فعال‌سازی سرویس

```bash
sudo systemctl daemon-reload
sudo systemctl enable keramat-bot.service
sudo systemctl start keramat-bot.service
sudo systemctl status keramat-bot.service
sudo journalctl -u keramat-bot.service -f
```

اگر فایل سرویس هنوز ساخته نشده، این نمونه را در `/etc/systemd/system/keramat-bot.service` قرار دهید. مسیر پایتون را با محیط سرور تطبیق دهید.

```ini
[Unit]
Description=Valedyar Bale bot
After=network-online.target
Wants=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Telegram-Bale-Bot/Quizbot
ExecStart=/home/ubuntu/Telegram-Bale-Bot/Quizbot/venv/bin/python main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

> `PYTHONUNBUFFERED=1` باعث می‌شود خروجی `print` بلافاصله در `journalctl` دیده شود.

### به‌روزرسانی کد روی سرور

```bash
cd /home/ubuntu/Telegram-Bale-Bot
cp Quizbot/database/keramat.db ~/keramat.db.$(date +%F).bak   # پشتیبان دیتابیس
git pull origin main
cd Quizbot
source venv/bin/activate        # اگر روی سرور از venv استفاده می‌کنید
pip install -r requirements.txt
python verify.py
sudo systemctl restart keramat-bot.service
sudo journalctl -u keramat-bot.service -f
```

بعد از شروع ربات، در لاگ باید یکی از دو خط زیر را ببینید:
- `Channel found`: دسترسی به کانال درست است.
- `Cannot access channel`: شناسهٔ کانال یا ادمین بودن ربات را بررسی کنید.

---

## ه) توضیح ماژول‌ها

### فایل‌های اصلی

- **`main.py`**
  نقطهٔ ورود برنامه. همهٔ پیام‌ها و callbackها اینجا دریافت می‌شوند و بر اساس state کاربر به handler مناسب می‌روند. بررسی دکمه‌های قدیمی، بررسی عضویت قبل از ثبت پاسخ و lock ضد دوبار زدن هم اینجاست.
- **`config.py`**
  متغیرهای محیطی را از `.env` بارگذاری می‌کند و مسیرها و متن‌های ثابت ربات (خوش‌آمد، پیام‌های خطا و غیره) را تعریف می‌کند.
- **`bot_instance.py`**
  تنها نمونهٔ (singleton) `Client` بالیتون. در ماژول جداگانه است تا import حلقوی پیش نیاید.
- **`scheduler.py`**
  ارسال روزانهٔ پیام‌های چرخشی به همهٔ کاربران با APScheduler. **فعلاً غیرفعال است.** فراخوانی `start_scheduler()` در `main.py` کامنت شده است.
- **`verify.py`**
  تست خودکار آفلاین. همهٔ ماژول‌ها را import می‌کند و مسیر کاربر و ادمین را با دیتابیس موقت و بات شبیه‌سازی‌شده اجرا می‌کند.

### `handlers/`: جریان کاربر

- **`membership.py`:** بررسی عضویت کاربر در کانال با `get_chat_member`. اگر خطا رخ دهد، کاربر غیرعضو در نظر گرفته می‌شود.
- **`registration.py`:** پیام خوش‌آمد همراه دکمهٔ عضویت، دریافت یا رد کردن شماره تماس، و شروع سؤالات مقدماتی.
- **`intro.py`:** سؤالات مقدماتی (وضعیت تأهل و جنسیت فرزند). این سؤالات `role`، `gender`، `children` و کلید محصولات پیشنهادی را جمع می‌کنند.
- **`quiz.py`:** پنج سؤال اصلی. هر پاسخ یک کد (۱ تا ۵) ثبت می‌کند. دکمه‌های قدیمی پذیرفته نمی‌شوند.
- **`result.py`:** تعیین تیپ (پرتکرارترین کد)، ارسال تصویر و توضیح، پیشنهاد محصول و لینک دعوت.
- **`prize_info.py`:** متنی را که برندهٔ قرعه‌کشی بعد از پیام جایزه می‌فرستد، یک بار به‌عنوان مشخصاتش ذخیره می‌کند.
- **`states.py`:** ثابت‌های state (`new`، `await_join`، `await_phone`، `intro`، `quiz`، `done`) و توابع کمکی مثل `can_answer` و `build_display_name`.

### `admin/`: پنل ادمین

- **`handlers.py`:** مسیریابی callbackهای `admin:*` و پیام‌های متنی ادمین در حالت‌های ویژه (پیام همگانی، تعداد قرعه‌کشی، متن جایزه).
- **`stats.py`:** آمار کلی کاربران، دعوت‌ها و توزیع نتایج.
- **`broadcast.py`:** ارسال یک پیام به همهٔ کاربران با فاصلهٔ زمانی بین ارسال‌ها.
- **`export.py`:** خروجی اکسل کاربران، دعوت‌کنندگان و برندگان.
- **`graph.py`:** تصویر شبکهٔ دعوت با `networkx` و `matplotlib`.
- **`prize.py`:** سه نوع قرعه‌کشی، فهرست برندگان به ترتیب رتبه، و ارسال پیام جایزه و ثبت برندگان.
- **`logs.py`:** نمایش آخرین اقدامات ادمین‌ها.

### سایر پوشه‌ها

- **`keyboards/builders.py`:** همهٔ کیبوردهای inline (کاربر و ادمین).
- **`data/`:** فایل‌های اکسل محتوا (`content.py` آن‌ها را یک بار بارگذاری می‌کند و `loaders.py` آن‌ها را می‌خواند).
- **`database/db.py`:** لایهٔ SQLite با `aiosqlite`. جدول‌ها: `users`، `invites`، `invited_users`، `admin_logs` و `lottery_winners`.
- **`utils/`:** توابع کمکی (`to_persian_digits`، `safe_answer`) و دکوراتورهای دسترسی ادمین.

### فایل‌های محتوا (`data/*.xlsx`)

متن سؤالات، نتایج و محصولات **دستی** در این فایل‌ها نگهداری می‌شوند. بعد از هر تغییر باید ربات را ری‌استارت کنید.

| فایل | ستون‌ها |
|---|---|
| `INTRO.xlsx` | `q_key`, `q_text`, `opt_text`, `role`, `gender`, `children`, `product_key` |
| `QUESTIONS.xlsx` | `q_index`, `q_text`, `opt_label`, `opt_text`, `code` |
| `RESULT_TEXTS.xlsx` | `code`, `title`, `nickname`, `description` |
| `RESULT_IMAGES.xlsx` | `code`, `image` |
| `PRODUCTS.xlsx` | `product_key`, `name`, `url` |

- **تصاویر:** برای هر تصویر (مثلاً `Borj.png`) دو فایل `Borj_female.png` و `Borj_male.png` باید در `pics/` وجود داشته باشد.
- **طول متن نتیجه:** توضیح هر تیپ همراه عنوانش زیر تصویر ارسال می‌شود و مجموع آن باید **کمتر از ۱۰۲۴ نویسه** باشد.
- **آدرس محصولات:** آدرس‌ها باید با `https://` شروع شوند.

### پنل ادمین

ادمین‌ها (شناسه‌های داخل `ADMIN_IDS`) با فرمان `/admin` وارد پنل می‌شوند. گزینه‌ها:
- **📊 آمار**
- **📨 پیام همگانی**
- **📁 خروجی اکسل**
- **📈 نمودار دعوت‌ها**
- **🎁 جوایز:** قرعه‌کشی، ارسال پیام جایزه و مشخصات برندگان
- **📋 لاگ‌ها**

**نکته‌ها:**
- **لینک دعوت:** فقط برای کاربری حساب می‌شود که **اولین بار** وارد ربات می‌شود و عضویتش در کانال تأیید شده است.
- **لغو عملیات:** اگر وسط یک عملیات ادمین یک فرمان مثل `/start` بفرستید، عملیات لغو می‌شود.

---

## و) نکات مهم

> ⚠️ **امنیت توکن:** توکن قدیمی ربات در تاریخچهٔ git مخزن هست. آن را از BotFather باطل کنید و توکن جدید بگیرید. هر بار هم که توکن جایی منتشر شد (commit، اسکرین‌شات، پیام)، همین کار را تکرار کنید. راهنمای پاک کردن تاریخچه در `SECURITY_CLEANUP.md` در ریشهٔ مخزن است.

> ⚠️ **اسکریپت `tools/build_excels.py` حذف شده است.** داده‌های اکسل را دستی در پوشهٔ `data/` نگهداری کنید.

> ⚠️ **فایل `.env` را هرگز commit نکنید.** این فایل در `.gitignore` هست.

> ⚠️ **این فایل‌ها را commit نکنید:** `__pycache__/`، `*.pyc`، `*.db`، `export_*.xlsx` و `graph_*.png`. همه در `.gitignore` هستند.

> ⚠️ **قبل از هر deploy، `verify.py` را اجرا کنید.** این اسکریپت از دیتابیس موقت استفاده می‌کند و پیامی ارسال نمی‌کند، پس اجرایش روی سرور هم امن است.

---

## ز) ساختار پوشه‌ها

```
Quizbot/
├── main.py
├── bot_instance.py
├── config.py
├── scheduler.py
├── verify.py
├── requirements.txt
├── README_FA.md
├── CHANGELOG.md
├── admin/
│   ├── handlers.py
│   ├── stats.py
│   ├── broadcast.py
│   ├── export.py
│   ├── graph.py
│   ├── prize.py
│   └── logs.py
├── handlers/
│   ├── membership.py
│   ├── registration.py
│   ├── intro.py
│   ├── quiz.py
│   ├── result.py
│   ├── prize_info.py
│   └── states.py
├── keyboards/
│   └── builders.py
├── data/
│   ├── content.py
│   ├── loaders.py
│   ├── INTRO.xlsx
│   ├── QUESTIONS.xlsx
│   ├── RESULT_TEXTS.xlsx
│   ├── RESULT_IMAGES.xlsx
│   └── PRODUCTS.xlsx
├── database/
│   └── db.py
├── utils/
│   ├── helpers.py
│   └── decorators.py
└── pics/
    ├── <Type>_female.png / <Type>_male.png
    └── invite.jpg
```

در هر پوشهٔ پایتون یک فایل `__init__.py` هم هست که برای خلاصه بودن نمودار نشان داده نشده است.

---

## ح) لایسنس و اعتبار

- **لایسنس:** Private
- **توسعه‌دهنده:** CodeNomad84
- **مخزن:** https://github.com/CodeNomad84/Telegram-Bale-Bot
