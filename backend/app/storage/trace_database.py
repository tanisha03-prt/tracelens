
import sqlite3
from pathlib import Path


# Database file location
DATABASE_PATH = Path(__file__).resolve().parent / "traces.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL
            )
        """)


def register_trace(trace_id: str, status: str, file_path: str):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO traces
                (trace_id, status, file_path)
            VALUES (?, ?, ?)
            """,
            (trace_id, status, file_path)
        )


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at: {DATABASE_PATH}")
