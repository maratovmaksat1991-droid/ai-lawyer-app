import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "legal_os.db")


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицу cases, если она не существует."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            module TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_case(title, module, content):
    """Сохраняет дело в базу."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO cases (title, module, content, created_at) VALUES (?, ?, ?, ?)",
        (title, module, content, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()


def get_cases(limit=50):
    """Возвращает список дел (новые сверху)."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM cases ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_case(case_id):
    """Возвращает одно дело по ID."""
    conn = _get_connection()
    row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_case(case_id):
    """Удаляет дело по ID."""
    conn = _get_connection()
    conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    conn.commit()
    conn.close()


# Инициализация при импорте
init_db()
