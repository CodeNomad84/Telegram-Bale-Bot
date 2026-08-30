import aiosqlite
from config import DB_PATH


async def get_stats_text():
    async with aiosqlite.connect(DB_PATH) as db:
        # Total users
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total = (await cursor.fetchone())[0]

        # Completed (state = 'done')
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE state = 'done'")
        completed = (await cursor.fetchone())[0]

        # In progress (state = 'intro' or 'quiz')
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE state IN ('intro', 'quiz')")
        in_progress = (await cursor.fetchone())[0]

        # Unique inviters
        cursor = await db.execute("SELECT COUNT(*) FROM invites")
        inviters = (await cursor.fetchone())[0]

        # Total invites
        cursor = await db.execute("SELECT SUM(count) FROM invites")
        total_invites = (await cursor.fetchone())[0] or 0

        # Result distribution
        cursor = await db.execute(
            "SELECT result_title, COUNT(*) FROM users WHERE result_title IS NOT NULL GROUP BY result_title"
        )
        results = await cursor.fetchall()
        result_lines = "\n".join(f"  • {title}: {count}" for title, count in results) if results else "  • هیچ داده‌ای"

    return (
        f"📊 **آمار کلی**\n\n"
        f"👥 کل کاربران: {total}\n"
        f"✅ تکمیل‌کنندگان: {completed}\n"
        f"⏳ در حال پاسخ‌دهی: {in_progress}\n"
        f"📨 تعداد دعوت‌کننده‌ها: {inviters}\n"
        f"📬 مجموع دعوت‌ها: {total_invites}\n\n"
        f"📈 **توزیع نتایج**:\n{result_lines}"
    )