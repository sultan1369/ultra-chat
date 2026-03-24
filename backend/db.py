import sqlite3

def get_db():
    conn = sqlite3.connect("chat.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        msg TEXT
    )
    """)
    return conn