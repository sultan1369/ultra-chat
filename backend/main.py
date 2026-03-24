from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, time, os

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 ACTIVE CLIENTS (REAL-TIME)
clients = {}

# ✅ DB FILE
DB = "chat.db"

# ✅ DB CONNECT
def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

# ✅ INIT DB
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

    # 🔥 INDEX FOR SPEED
    c.execute("CREATE INDEX IF NOT EXISTS idx_receiver ON messages(receiver)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_time ON messages(time)")

    conn.commit()
    conn.close()

init_db()

# 🔥 AUTO DELETE (5 HOURS)
def cleanup():
    conn = get_db()
    c = conn.cursor()

    expiry = int(time.time()) - 18000
    c.execute("DELETE FROM messages WHERE time < ?", (expiry,))

    conn.commit()
    conn.close()

# =========================
# 📡 WEBSOCKET (REAL-TIME)
# =========================
@app.websocket("/ws/{user}")
async def websocket_endpoint(ws: WebSocket, user: str):
    await ws.accept()
    clients[user] = ws

    try:
        while True:
            data = await ws.receive_json()

            s = data["s"]
            r = data["r"]
            m = data["m"][:40]
            t = int(time.time())

            cleanup()

            # 💾 SAVE
            conn = get_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO messages (sender, receiver, msg, time) VALUES (?, ?, ?, ?)",
                (s, r, m, t)
            )
            conn.commit()
            conn.close()

            # ⚡ SEND TO RECEIVER
            if r in clients:
                await clients[r].send_json({
                    "id": None,
                    "s": s,
                    "m": m,
                    "t": t
                })

    except WebSocketDisconnect:
        clients.pop(user, None)

# =========================
# 📤 HTTP SEND (BACKUP)
# =========================
class Message(BaseModel):
    s: str
    r: str
    m: str
    t: int

@app.post("/s")
def send(msg: Message):
    cleanup()

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO messages (sender, receiver, msg, time) VALUES (?, ?, ?, ?)",
        (msg.s, msg.r, msg.m[:40], msg.t)
    )

    conn.commit()
    conn.close()

    return {"ok": 1}

# =========================
# 📥 FETCH (OPTIONAL BACKUP)
# =========================
@app.get("/r/{user}/{last_id}")
def receive(user: str, last_id: int):
    cleanup()

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT id, sender, msg, time
        FROM messages
        WHERE id > ? AND (sender=? OR receiver=?)
    """, (last_id, user, user))

    data = c.fetchall()
    conn.close()

    return data

# =========================
# ❤️ HEALTH
# =========================
@app.get("/")
def home():
    return {"status": "running"}

# =========================
# 🚀 RUN (RENDER)
# =========================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)