import sqlite3
from config import DB_PATH


def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            thread_id TEXT PRIMARY KEY,
            summary   TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id  TEXT NOT NULL REFERENCES conversations(thread_id),
            role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content    TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.close()


def ensure_conversation(thread_id: str):
    conn = _connect()
    conn.execute(
        "INSERT OR IGNORE INTO conversations (thread_id) VALUES (?)",
        (thread_id,),
    )
    conn.commit()
    conn.close()


def add_message(thread_id: str, role: str, content: str):
    ensure_conversation(thread_id)
    conn = _connect()
    conn.execute(
        "INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)",
        (thread_id, role, content),
    )
    conn.commit()
    conn.close()


def get_messages(thread_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE thread_id = ? ORDER BY id",
        (thread_id,),
    ).fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def get_message_count(thread_id: str) -> int:
    conn = _connect()
    count = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE thread_id = ?",
        (thread_id,),
    ).fetchone()[0]
    conn.close()
    return count


def get_summary(thread_id: str) -> str:
    conn = _connect()
    row = conn.execute(
        "SELECT summary FROM conversations WHERE thread_id = ?",
        (thread_id,),
    ).fetchone()
    conn.close()
    return row["summary"] if row else ""


def update_summary_and_trim(thread_id: str, summary: str, trim_count: int):
    conn = _connect()
    conn.execute(
        "UPDATE conversations SET summary = ?, updated_at = CURRENT_TIMESTAMP WHERE thread_id = ?",
        (summary, thread_id),
    )
    conn.execute(
        """DELETE FROM messages WHERE id IN (
            SELECT id FROM messages WHERE thread_id = ? ORDER BY id LIMIT ?
        )""",
        (thread_id, trim_count),
    )
    conn.commit()
    conn.close()
