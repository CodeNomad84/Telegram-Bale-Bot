from database.db import get_admin_logs


async def get_logs_text(limit=50):
    logs = await get_admin_logs(limit)
    if not logs:
        return "📋 هیچ لاگی ثبت نشده است."

    lines = []
    for log in logs:
        lines.append(
            f"🕒 {log['created_at']}\n👤 {log['admin_id']}\n🔹 {log['action']}\n📄 {log['details'] or '-'}\n"
        )
    return "📋 **لاگ‌های اخیر**\n\n" + "\n".join(lines[:limit])