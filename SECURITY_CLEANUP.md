# راهنمای پاکسازی اطلاعات حساس از تاریخچهٔ git

> ⚠️ **هنوز چیزی اجرا نشده است.** بازنویسی تاریخچه hash همهٔ کامیت‌ها را عوض می‌کند و بعد از push به GitHub برگشت ساده ندارد. این راهنما را کامل بخوانید و بعد اسکریپت را اجرا کنید.

اسکریپت خودکار: [`cleanup_history.sh`](cleanup_history.sh) در ریشهٔ مخزن.

---

## ۱. چه چیزهایی در تاریخچه هست و پاک می‌شود

این مسیرها در کامیت‌های قدیمی مخزن هستند و روی GitHub هم push شده‌اند:

| الگوی حذف | مسیرهای پیداشده در تاریخچه | محتوا |
|---|---|---|
| `.env` | `.env` | توکن ربات و شناسهٔ ادمین‌ها |
| `*.db` | `database/keramat.db`، `Quizbot/database/keramat.db` | دیتابیس کاربران (شماره تلفن) |
| `*.pem`، `*.ppk` | در تاریخچه پیدا نشد؛ برای اطمینان حذف می‌شود | کلید خصوصی سرور |
| `*.sqlite3` | در تاریخچه پیدا نشد؛ برای اطمینان حذف می‌شود | دیتابیس |
| `*export_users_*.xlsx` | ۲ فایل در ریشه و ۲ فایل در `Quizbot/` | خروجی کاربران (شماره تلفن) |
| `*graph_*.png` | ۲ فایل در ریشه | نمودار دعوت (شناسهٔ کاربران) |

> دو الگوی آخر جزو فهرست اولیه (`.env`، `keramat.db`، `*.pem`، `*.ppk`) نبودند. چون همان اطلاعات شخصی را دارند، به اسکریپت اضافه شدند. اگر نمی‌خواهید پاک شوند، دو خط مربوط را از `FILTER_ARGS` در اسکریپت حذف کنید.

**چیزهایی که دست نمی‌خورند:**
- **کد و محتوا:** همهٔ کدها، اکسل‌های `data/`، تصاویر و مستندات.
- **`.env.local.example`:** اسکریپت بعد از اجرا وجود آن را بررسی می‌کند.
- **فایل‌های محلی:** `.env` و `keramat.db` روی دیسک. این‌ها ignore هستند و filter-repo فقط تاریخچه را عوض می‌کند. برای اطمینان، اسکریپت قبل از اجرا از آن‌ها کپی هم می‌گیرد.

---

## ۲. پیش‌نیازها: قبل از اجرا آماده باشد

| ✓ | مورد | چطور |
|---|---|---|
| □ | **توکن ربات عوض شده** | از `@BotFather`. پاک کردن تاریخچه توکنی را که منتشر شده باطل نمی‌کند. |
| □ | **git-filter-repo نصب است** | `pip install git-filter-repo`، بعد `git filter-repo --version` یا `python -m git_filter_repo --version` |
| □ | **روی branch اصلاحات هستید** | `git checkout fix/claude-review-fixes`. روی main فایل `.gitignore` هنوز UTF-16 و بی‌اثر است. |
| □ | **working tree تمیز است و stash ندارید** | `git status` و `git stash list` هر دو خالی باشند |
| □ | **main محلی با GitHub همگام است** | `git fetch origin` و بعد `git status main`. remote نباید کامیتی داشته باشد که محلی ندارید. |
| □ | **اجازهٔ force-push روی main دارید** | اگر در GitHub برای main «Branch protection» فعال است، موقتاً force-push را مجاز کنید. |
| □ | **همکاران خبر دارند** | هر clone دیگر بعد از این کار باید دوباره clone شود |
| □ | **فضای کافی کنار مخزن هست** | پوشهٔ پشتیبان در پوشهٔ والد مخزن ساخته می‌شود |

---

## ۳. اجرا

در **Git Bash** (ویندوز) یا ترمینال لینوکس، داخل مخزن:

```bash
bash cleanup_history.sh
```

مراحل اسکریپت:

0. **بررسی پیش‌نیازها:** filter-repo نصب باشد، branch درست باشد، tree تمیز باشد، و main محلی شامل main روی GitHub باشد. اگر هر کدام برقرار نباشد، اسکریپت بدون هیچ تغییری متوقف می‌شود.
1. **نمایش فهرست فایل‌هایی که پاک می‌شوند** و پرسیدن ← **تأیید ۱** (`yes`)
2. **پشتیبان کامل** در `../history-backup-<زمان>/`، شامل:
   - `repo-before-cleanup.bundle`: کل مخزن با همهٔ branchها
   - `refs-before-cleanup.txt`: hash قبلی همهٔ refها
   - کپی `.env` و `keramat.db`
3. **بازنویسی تاریخچه** با `git filter-repo --force`
4. **بررسی نتیجه:**
   - هیچ مسیر حساسی در `git log --all` نمانده باشد
   - `git log --all --full-history -- .env` خالی باشد
   - branch اصلاحات روی main جدید باشد
   - `.env.local.example` و فایل‌های محلی سالم باشند
5. **نمایش main جدید** و پرسیدن ← **تأیید ۲** (`yes`)، بعد `git push --force-with-lease` روی **فقط main**.
   - `--force-with-lease` فقط وقتی push می‌کند که main روی GitHub از لحظهٔ شروع تغییر نکرده باشد.
   - اگر در تأیید ۲ `no` بزنید، تاریخچهٔ محلی پاک می‌ماند و دستور push برای بعد چاپ می‌شود.

**branch اصلاحات push نمی‌شود.** آن را بعد از بررسی خودتان push کنید.

### آیا branch اصلاحات باید rebase شود؟

**خیر.** اسکریپت filter-repo را روی همین مخزن کاری اجرا می‌کند (نه روی یک clone جدا). filter-repo **همهٔ branchهای محلی را با هم** بازنویسی می‌کند، پس `fix/claude-review-fixes` خودکار روی main جدید قرار می‌گیرد. اسکریپت این را با `git merge-base --is-ancestor main fix/claude-review-fixes` بررسی می‌کند.

rebase فقط برای **clone دیگری** لازم است که branch محلی push‌نشده دارد. ساده‌ترین راه، clone دوباره است. اگر لازم شد، hash قدیم و جدید هر کامیت در فایل `.git/filter-repo/commit-map` همین مخزن هست:

```bash
# در clone دیگر، بعد از force-push:
git fetch origin
git rebase --onto origin/main <hash-قدیم-main> <branch-محلی>
```

### معادل دستی (برای مرجع)

اسکریپت همین دستور را اجرا می‌کند:

```bash
git filter-repo --force --invert-paths \
  --path .env \
  --path-glob '*.db' \
  --path-glob '*.sqlite3' \
  --path-glob '*.pem' \
  --path-glob '*.ppk' \
  --path-glob '*export_users_*.xlsx' \
  --path-glob '*graph_*.png'

git remote add origin https://github.com/CodeNomad84/Telegram-Bale-Bot.git   # filter-repo آن را حذف می‌کند
git push --force-with-lease=main:<hash-قبلی-origin/main> origin main
```

---

## ۴. بعد از اجرا

1. **بررسی نتیجه:** خروجی دستور زیر باید خالی باشد.
   ```bash
   git log --all --full-history -- .env
   ```
2. **روی سرور هرگز `git pull` نزنید.** pull تاریخچهٔ قدیم را دوباره ادغام می‌کند. این مرحله را هر وقت به سرور وصل شدید انجام دهید. اجرای اسکریپت روی سیستم محلی به سرور دست نمی‌زند.
   ```bash
   cd /home/ubuntu/Telegram-Bale-Bot
   # اول پشتیبان از دیتابیس واقعی و .env روی سرور
   cp Quizbot/database/keramat.db ~/keramat.db.$(date +%F).bak
   cp .env ~/env.$(date +%F).bak
   git fetch origin
   git reset --hard origin/main
   sudo systemctl restart keramat-bot.service
   ```
   `.env` و `keramat.db` روی سرور ignore هستند و با `reset --hard` دست نمی‌خورند.
3. **push کردن branch اصلاحات** (بعد از بررسی):
   ```bash
   git push -u origin fix/claude-review-fixes
   ```
4. **clone‌های دیگر:** هر clone دیگری را (سیستم دیگر، همکاران) دوباره clone کنید.
5. **کش GitHub:**
   - کامیت‌های قدیمی تا مدتی با hash مستقیم روی GitHub قابل دسترس می‌مانند. برای حذف کامل از GitHub Support درخواست کنید (راهنمای «Removing sensitive data from a repository» در مستندات GitHub).
   - اگر مخزن public بوده، فرض کنید داده‌ها کپی شده‌اند. fork‌ها تاریخچهٔ قدیم را نگه می‌دارند.
   - مخزن را **private** کنید.
6. **حذف پشتیبان:** بعد از اطمینان از موفقیت، پوشهٔ `history-backup-*` را پاک کنید. این پوشه توکن و دیتابیس را دارد و **هرگز نباید آپلود شود**.

---

## ۵. اگر مشکلی پیش آمد (بازیابی)

**قبل از push** (یعنی اسکریپت در تأیید ۲ متوقف شده یا خطا داده): کل مخزن از bundle قابل بازیابی است.

```bash
cd ..
git clone history-backup-<زمان>/repo-before-cleanup.bundle Keramat_Quizbot2-restored
cd Keramat_Quizbot2-restored
git checkout fix/claude-review-fixes
git remote set-url origin https://github.com/CodeNomad84/Telegram-Bale-Bot.git
cp ../history-backup-<زمان>/.env .
```

**بعد از push:** همان bundle تاریخچهٔ قدیم را دارد، ولی برگرداندن آن به GitHub یعنی انتشار دوبارهٔ اطلاعات حساس. این کار را نکنید.
