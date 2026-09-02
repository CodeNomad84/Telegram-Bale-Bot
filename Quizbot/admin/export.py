import json
import aiosqlite
from openpyxl import Workbook
from config import DB_PATH
from datetime import datetime


async def export_users_excel():
    """Export all user data to an Excel file."""
    file_path = f"git rm --cached export_users_*.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Users"

    # Headers
    headers = ["user_id", "username", "display_name", "phone", "role", "gender",
               "children", "answers", "result_code", "result_title", "state", "created_at"]
    ws.append(headers)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, username, display_name, phone, role, gender, children, "
            "answers, result_code, result_title, state, created_at FROM users"
        )
        rows = await cursor.fetchall()
        for row in rows:
            # Convert answers JSON to string
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

    wb.save(file_path)
    return file_path