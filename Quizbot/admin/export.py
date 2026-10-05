"""Export all users and inviters to an Excel file with two sheets."""

import json
import aiosqlite
from openpyxl import Workbook
from datetime import datetime

from config import DB_PATH


async def export_users_excel():
    """تولید فایل اکسل با دو شیت: کاربران و دعوت‌کنندگان."""
    file_path = f"export_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = Workbook()

    # ---------- شیت ۱: کاربران ----------
    ws = wb.active
    ws.title = "Users"
    headers = [
        "user_id", "username", "display_name", "phone", "role", "gender",
        "children", "answers", "result_code", "result_title", "state", "created_at"
    ]
    ws.append(headers)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, username, display_name, phone, role, gender, children, "
            "answers, result_code, result_title, state, created_at FROM users"
        )
        rows = await cursor.fetchall()
        for row in rows:
            answers = json.loads(row["answers"]) if row["answers"] else []
            ws.append([
                row["user_id"],
                row["username"],
                row["display_name"],
                row["phone"],
                row["role"],
                row["gender"],
                row["children"],
                ", ".join(str(a) for a in answers),
                row["result_code"],
                row["result_title"],
                row["state"],
                row["created_at"],
            ])

    # ---------- شیت ۲: دعوت‌کنندگان ----------
    ws2 = wb.create_sheet("Inviters")
    ws2.append(["inviter_id", "username", "display_name", "phone", "invite_count"])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT i.inviter_id, i.count, u.username, u.display_name, u.phone
               FROM invites i
               LEFT JOIN users u ON u.user_id = i.inviter_id
               ORDER BY i.count DESC"""
        )
        inviter_rows = await cursor.fetchall()
        for row in inviter_rows:
            ws2.append([
                row["inviter_id"],
                row["username"],
                row["display_name"],
                row["phone"],
                row["count"],
            ])

    wb.save(file_path)
    return file_path