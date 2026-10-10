"""SQLite persistence for Student Planner assessments."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta


SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    module TEXT NOT NULL,
    due_date TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
)
"""


@contextmanager
def connect(database_path: str):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.close()


def init_database(database_path: str) -> None:
    with connect(database_path) as connection:
        connection.execute(SCHEMA)


def create_task(database_path: str, values: dict) -> int:
    with connect(database_path) as connection:
        cursor = connection.execute(
            """INSERT INTO tasks
               (title, description, module, due_date, priority, completed, created_at)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (values["title"], values["description"], values["module"],
             values["due_date"], values["priority"], date.today().isoformat()),
        )
        return cursor.lastrowid


def get_task(database_path: str, task_id: int):
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()


def update_task(database_path: str, task_id: int, values: dict) -> bool:
    with connect(database_path) as connection:
        cursor = connection.execute(
            """UPDATE tasks SET title = ?, description = ?, module = ?,
               due_date = ?, priority = ? WHERE id = ?""",
            (values["title"], values["description"], values["module"],
             values["due_date"], values["priority"], task_id),
        )
        return cursor.rowcount > 0


def toggle_task(database_path: str, task_id: int):
    task = get_task(database_path, task_id)
    if task is None:
        return None
    with connect(database_path) as connection:
        connection.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (0 if task["completed"] else 1, task_id),
        )
    return get_task(database_path, task_id)


def delete_task(database_path: str, task_id: int) -> bool:
    with connect(database_path) as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0


def list_tasks(database_path: str, filters: dict | None = None):
    filters = filters or {}
    clauses = []
    parameters = []
    if filters.get("module"):
        clauses.append("module = ?")
        parameters.append(filters["module"])
    if filters.get("priority"):
        clauses.append("priority = ?")
        parameters.append(filters["priority"])
    if filters.get("status") == "completed":
        clauses.append("completed = 1")
    elif filters.get("status") == "remaining":
        clauses.append("completed = 0")
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=7)).isoformat()
    if filters.get("deadline") == "overdue":
        clauses.append("completed = 0 AND due_date < ?")
        parameters.append(today)
    elif filters.get("deadline") == "soon":
        clauses.append("completed = 0 AND due_date BETWEEN ? AND ?")
        parameters.extend([today, soon])

    order = (
        "CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, due_date"
        if filters.get("sort") == "priority"
        else "completed, due_date, CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END"
    )
    query = "SELECT * FROM tasks"
    if clauses:
        query += " WHERE " + " AND ".join(f"({clause})" for clause in clauses)
    query += f" ORDER BY {order}, created_at"
    with connect(database_path) as connection:
        return connection.execute(query, parameters).fetchall()


def planner_statistics(database_path: str) -> dict:
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=7)).isoformat()
    with connect(database_path) as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS total,
               SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) AS remaining,
               SUM(CASE WHEN completed = 0 AND due_date < ? THEN 1 ELSE 0 END) AS overdue,
               SUM(CASE WHEN completed = 0 AND due_date BETWEEN ? AND ? THEN 1 ELSE 0 END) AS due_soon
               FROM tasks""",
            (today, today, soon),
        ).fetchone()
    stats = {key: row[key] or 0 for key in row.keys()}
    stats["progress"] = round(stats["completed"] / stats["total"] * 100) if stats["total"] else 0
    return stats
