from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, time, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}
DB = "chat.db"

def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

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

    conn.commit()
    conn.close()

init_db()

def cleanup():
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE time < ?", (int(time.time()) - 18000,))
    conn.commit()
    conn.close()

# 🔥 WEBSOCKET (REAL-TIME)
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

            conn = get_db()
            c = conn.cursor()

            c.execute(
                "INSERT INTO messages (sender, receiver, msg, time) VALUES (?, ?, ?, ?)",
                (s, r, m, t)
            )

            msg_id = c.lastrowid
            conn.commit()
            conn.close()

            payload = {
                "id": msg_id,
                "s": s,
                "m": m,
                "t": t
            }

            # ✅ SEND TO BOTH USERS
            if s in clients:
                await clients[s].send_json(payload)

            if r in clients:
                await clients[r].send_json(payload)

    except WebSocketDisconnect:
        clients.pop(user, None)

# 🔥 OFFLINE SYNC
@app.get("/sync/{user}/{last_id}")
def sync(user: str, last_id: int):

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

# ❤️ HEALTH
@app.get("/")
def home():
    return {"status": "running"}

# 🚀 RUN
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)