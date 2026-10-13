"""Export all users, inviters, and lottery winners to an Excel file."""

import json
import aiosqlite
from openpyxl import Workbook
from datetime import datetime

from config import DB_PATH
from database.db import get_all_lottery_winners


async def export_users_excel():
    """تولید فایل اکسل با سه شیت: کاربران، دعوت‌کنندگان، برندگان."""
    file_path = f"export_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = Workbook()

    # ---------- شیت ۱: کاربران ----------
    ws = wb.active
    ws.title = "Users"
    ws.append([
        "user_id", "username", "display_name", "phone", "role", "gender",
        "children", "answers", "result_code", "result_title", "state", "created_at"
    ])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, username, display_name, phone, role, gender, children, "
            "answers, result_code, result_title, state, created_at FROM users"
        )
        for row in await cursor.fetchall():
            answers = json.loads(row["answers"]) if row["answers"] else []
            ws.append([
                row["user_id"], row["username"], row["display_name"], row["phone"],
                row["role"], row["gender"], row["children"],
                ", ".join(str(a) for a in answers),
                row["result_code"], row["result_title"], row["state"], row["created_at"],
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
        for row in await cursor.fetchall():
            ws2.append([
                row["inviter_id"], row["username"], row["display_name"],
                row["phone"], row["count"],
            ])

    # ---------- شیت ۳: برندگان قرعه‌کشی ----------
    ws3 = wb.create_sheet("Lottery_Winners")
    ws3.append([
        "user_id", "username", "display_name", "phone",
        "category", "prize_sent_at", "info_text", "info_collected_at"
    ])
    winners = await get_all_lottery_winners()
    for w in winners:
        ws3.append([
            w["user_id"], w["username"], w["display_name"], w["phone"],
            w["category"], w["prize_sent_at"],
            w["info_text"], w["info_collected_at"],
        ])

    wb.save(file_path)
    return file_path