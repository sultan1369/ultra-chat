from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MODEL
class Message(BaseModel):
    s: str
    r: str
    m: str
    t: int


DB = "chat.db"

# ✅ INIT DB
def init_db():
    conn = sqlite3.connect(DB)
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

    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DB)


# ✅ SEND
@app.post("/s")
def send(msg: Message):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO messages (sender, receiver, msg, time) VALUES (?, ?, ?, ?)",
        (msg.s, msg.r, msg.m[:50], msg.t)  # limit size 🔥
    )

    conn.commit()
    conn.close()

    return {"ok": 1}


# ✅ RECEIVE ONLY NEW MESSAGES
@app.get("/r/{user}/{last_id}")
def receive(user: str, last_id: int):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "SELECT id, sender, msg, time FROM messages WHERE receiver=? AND id>?",
        (user, last_id)
    )

    data = c.fetchall()
    conn.close()

    return data


@app.get("/")
def home():
    return {"status": "running"}


# ✅ RENDER PORT
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)