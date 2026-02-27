import sqlite3
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS team (
            user_id   INTEGER PRIMARY KEY,
            username  TEXT,
            name      TEXT,
            added_by  INTEGER,
            added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            token      TEXT UNIQUE NOT NULL,
            status     TEXT DEFAULT 'pending',
            from_id    INTEGER,
            from_name  TEXT,
            photo_id   TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auto_replies (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword   TEXT NOT NULL,
            reply     TEXT NOT NULL,
            match_type TEXT DEFAULT 'contains',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS autoreply_status (
            id      INTEGER PRIMARY KEY CHECK (id = 1),
            enabled INTEGER DEFAULT 1
        );

        INSERT OR IGNORE INTO autoreply_status (id, enabled) VALUES (1, 1);

        CREATE TABLE IF NOT EXISTS contacts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            telegram_id INTEGER,
            username   TEXT,
            phone      TEXT,
            label      TEXT DEFAULT 'general',
            notes      TEXT,
            added_by   INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS schedules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id     INTEGER NOT NULL,
            message     TEXT NOT NULL,
            send_at     TEXT NOT NULL,
            repeat      TEXT DEFAULT 'none',
            status      TEXT DEFAULT 'pending',
            created_by  INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_tags (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id   INTEGER NOT NULL,
            chat_name TEXT,
            tag       TEXT NOT NULL,
            added_by  INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, tag)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id    INTEGER,
            title      TEXT NOT NULL,
            content    TEXT NOT NULL,
            added_by   INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


init_db()
