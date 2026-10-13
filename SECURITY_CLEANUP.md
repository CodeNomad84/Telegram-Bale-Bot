# راهنمای پاکسازی اطلاعات حساس از تاریخچهٔ git

> ⚠️ این دستورات **اجرا نشده‌اند**. بازنویسی تاریخچه برگشت‌ناپذیر است و همهٔ hashهای کامیت را عوض می‌کند.

## چه چیزهایی در تاریخچه هست؟

| مسیر | محتوا | کامیت‌ها |
|---|---|---|
| `.env` | توکن ربات، شناسه ادمین‌ها | `9f6bf20`, `674a2f4`, `6b3c6d7`, `16c8b68` |
| `database/keramat.db`, `Quizbot/database/keramat.db` | دیتابیس کاربران (شماره تلفن) | ۱۰ کامیت |
| `export_users_*.xlsx`, `Quizbot/export_users_*.xlsx` | خروجی کاربران (شماره تلفن) | چند کامیت |
| `graph_*.png` | نمودار شبکه دعوت (شناسه کاربران) | چند کامیت |

مخزن روی GitHub push شده است: `https://github.com/CodeNomad84/Telegram-Bale-Bot`

## گام ۰ — فوری‌ترین کار: عوض کردن توکن

پاک کردن تاریخچه توکنی را که قبلاً منتشر شده **باطل نمی‌کند**. هر کسی ممکن است آن را کپی کرده باشد.

1. در بله به `@BotFather` بروید و توکن ربات را revoke/عوض کنید.
2. توکن جدید را در `.env` سرور بگذارید و سرویس را ری‌استارت کنید:
   ```bash
   sudo systemctl restart keramat-bot.service
   ```

## گام ۱ — پشتیبان‌گیری

```bash
# روی سرور: پشتیبان از دیتابیس و .env
cp /home/ubuntu/Telegram-Bale-Bot/Quizbot/database/keramat.db ~/keramat.db.backup
cp /home/ubuntu/Telegram-Bale-Bot/.env ~/env.backup

# روی سیستم خودتان: یک نسخهٔ کامل از مخزن فعلی
git clone --mirror https://github.com/CodeNomad84/Telegram-Bale-Bot.git Telegram-Bale-Bot-backup.git
```

## گام ۲ — نصب git-filter-repo

```bash
pip install git-filter-repo
```

## گام ۳ — بازنویسی تاریخچه (روی یک clone تازه)

```bash
git clone https://github.com/CodeNomad84/Telegram-Bale-Bot.git cleanup-repo
cd cleanup-repo

git filter-repo --invert-paths \
  --path .env \
  --path database/keramat.db \
  --path Quizbot/database/keramat.db \
  --path-glob '*export_users_*.xlsx' \
  --path-glob '*graph_*.png' \
  --path-glob '*.pem' \
  --path-glob '*.ppk'
```

بررسی کنید که چیزی باقی نمانده است (خروجی باید خالی باشد):

```bash
git log --all --format= --name-only | sort -u | grep -Ei '\.env$|\.db$|export_users_|graph_|\.pem$|\.ppk$'
```

## گام ۴ — push اجباری

`filter-repo` ریموت `origin` را حذف می‌کند؛ دوباره اضافه کنید:

```bash
git remote add origin https://github.com/CodeNomad84/Telegram-Bale-Bot.git
git push --force --all origin
git push --force --tags origin
```

## گام ۵ — به‌روزرسانی سرور و سایر clone‌ها

بعد از بازنویسی، `git pull` معمولی کار نمی‌کند. روی سرور:

```bash
cd /home/ubuntu/Telegram-Bale-Bot
git fetch origin
git reset --hard origin/main
sudo systemctl restart keramat-bot.service
```

فایل‌های `.env` و `keramat.db` چون ignore هستند، با `reset --hard` دست نمی‌خورند. ولی پشتیبان گام ۱ را تا اطمینان نگه دارید.

روی سیستم توسعه هم یا clone تازه بگیرید یا همین `fetch` + `reset --hard` را اجرا کنید. branchهای محلی قدیمی (مثل `fix/claude-review-fixes`) باید روی تاریخچهٔ جدید rebase شوند:

```bash
git rebase --onto origin/main <old-main-hash> fix/claude-review-fixes
```

## گام ۶ — کش GitHub

- اگر مخزن **public** بوده، فرض کنید داده‌ها کپی شده‌اند. fork‌ها و Pull Requestها تاریخچهٔ قدیم را نگه می‌دارند.
- برای حذف کامل کامیت‌های قدیمی از کش GitHub، از GitHub Support درخواست کنید
  (راهنما: «Removing sensitive data from a repository» در مستندات GitHub).
- بهتر است مخزن را **private** کنید.
