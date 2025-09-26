import sqlite3
import os

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at INTEGER,
    updated_at INTEGER,
    metadata JSON
)
"""

CREATE_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT,
    conv_id TEXT,
    msg_id TEXT PRIMARY KEY,
    msg_type TEXT,
    tools JSON,
    actions JSON,
    content JSON,
    status TEXT,
    created_at INTEGER,
    updated_at INTEGER,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
"""

CREATE_CONTEXT_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS context_messages (
    session_id TEXT PRIMARY KEY,
    context_data JSON,
    created_at INTEGER,
    updated_at INTEGER,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
"""


def initialize_sqlite(db_name="blaze.db"):
    """Initialize the SQLite database by creating the necessary tables."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute(CREATE_SESSIONS_TABLE)
    cursor.execute(CREATE_CONVERSATIONS_TABLE)
    cursor.execute(CREATE_CONTEXT_MESSAGES_TABLE)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_path = os.getenv("SQLITE_DB_PATH", "blaze.db")
    initialize_sqlite(db_path)