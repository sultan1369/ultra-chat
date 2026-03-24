from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import time
import os

app = FastAPI()

# ✅ CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MODEL (ultra-light payload)
class Message(BaseModel):
    s: str  # sender
    r: str  # receiver
    m: str  # message
    t: int  # timestamp


# ✅ DATABASE FILE
DB = "chat.db"


# ✅ GET DB CONNECTION (thread-safe)
def get_db():
    return sqlite3.connect(DB, check_same_thread=False)


# ✅ INIT DATABASE
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        msg TEXT,
        time INTEGER
    )
    """)

    # 🔥 INDEX for faster low-network queries
    c.execute("CREATE INDEX IF NOT EXISTS idx_receiver ON messages(receiver)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_time ON messages(time)")

    conn.commit()
    conn.close()


init_db()


# 🔥 AUTO DELETE (older than 5 hours)
def cleanup():
    conn = get_db()
    c = conn.cursor()

    now = int(time.time())
    expiry = now - 18000  # 5 hours

    c.execute("DELETE FROM messages WHERE time < ?", (expiry,))

    conn.commit()
    conn.close()


# ✅ SEND MESSAGE
@app.post("/s")
def send(msg: Message):
    cleanup()

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO messages (sender, receiver, msg, time) VALUES (?, ?, ?, ?)",
        (msg.s, msg.r, msg.m[:40], msg.t)  # limit size 🔥
    )

    conn.commit()
    conn.close()

    return {"ok": 1}


# ✅ RECEIVE ONLY NEW MESSAGES (LOW DATA)
@app.get("/r/{user}/{last_id}")
def receive(user: str, last_id: int):
    cleanup()

    conn = get_db()
    c = conn.cursor()

    c.execute(
        """
        SELECT id, sender, msg, time 
        FROM messages 
        WHERE id > ? AND (sender = ? OR receiver = ?)
        """,
        (last_id, user, user)
    )

    data = c.fetchall()
    conn.close()

    return data


# ✅ HEALTH CHECK
@app.get("/")
def home():
    return {"status": "running"}


# ✅ RENDER COMPATIBLE RUN
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)