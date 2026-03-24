from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

# ✅ CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MODEL (ultra small payload)
class Message(BaseModel):
    s: str  # sender
    r: str  # receiver
    m: str  # message
    t: int  # timestamp


# ✅ DB PATH (Render safe)
DB_PATH = "chat.db"


# ✅ INIT DB (auto run)
def init_db():
    conn = sqlite3.connect(DB_PATH)
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


# ✅ DB CONNECTION HELPER (important)
def get_db():
    return sqlite3.connect(DB_PATH)


# ✅ SEND MESSAGE
@app.post("/s")
def send(msg: Message):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO messages (sender, receiver, msg, time) VALUES (?, ?, ?, ?)",
        (msg.s, msg.r, msg.m, msg.t)
    )

    conn.commit()
    conn.close()

    return {"ok": 1}


# ✅ RECEIVE MESSAGES
@app.get("/r/{user}")
def receive(user: str):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "SELECT sender, msg, time FROM messages WHERE receiver=?",
        (user,)
    )

    data = c.fetchall()
    conn.close()

    return data


# ✅ ROOT (health check)
@app.get("/")
def home():
    return {"status": "running"}


# ✅ RENDER PORT HANDLING
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)