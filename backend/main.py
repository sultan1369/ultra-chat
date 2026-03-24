from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, time, os

app = FastAPI()

# 🌐 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 MULTI-CONNECTION SUPPORT (important fix)
clients = {}  # { user: [ws1, ws2] }

DB = "chat.db"


# 🔌 DB CONNECT
def get_db():
    return sqlite3.connect(DB, check_same_thread=False)


# 🏗 INIT DB
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

    # 🔥 INDEXES (speed boost)
    c.execute("CREATE INDEX IF NOT EXISTS idx_user ON messages(sender, receiver)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_time ON messages(time)")

    conn.commit()
    conn.close()


init_db()


# 🧹 CLEAN OLD DATA (5 HOURS)
def cleanup():
    conn = get_db()
    c = conn.cursor()

    expiry = int(time.time()) - 18000
    c.execute("DELETE FROM messages WHERE time < ?", (expiry,))

    conn.commit()
    conn.close()


# 📡 WEBSOCKET (REAL-TIME)
@app.websocket("/ws/{user}")
async def websocket_endpoint(ws: WebSocket, user: str):

    await ws.accept()

    # ✅ support multiple devices per user
    if user not in clients:
        clients[user] = []
    clients[user].append(ws)

    try:
        while True:
            data = await ws.receive_json()

            s = data.get("s")
            r = data.get("r")
            m = data.get("m", "")[:40]
            t = int(time.time())

            cleanup()

            # 💾 STORE MESSAGE
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

            # 🔥 SEND TO BOTH USERS (ALL DEVICES)
            for u in [s, r]:
                if u in clients:
                    for client in clients[u]:
                        try:
                            await client.send_json(payload)
                        except:
                            pass  # ignore broken connections

    except WebSocketDisconnect:
        if user in clients:
            clients[user].remove(ws)
            if not clients[user]:
                del clients[user]


# 🔄 OFFLINE SYNC (BACKUP)
@app.get("/sync/{user}/{last_id}")
def sync(user: str, last_id: int):

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT id, sender, msg, time
        FROM messages
        WHERE id > ? AND (sender=? OR receiver=?)
        ORDER BY id ASC
    """, (last_id, user, user))

    data = c.fetchall()
    conn.close()

    return data


# ❤️ HEALTH CHECK
@app.get("/")
def home():
    return {"status": "running"}


# 🚀 RUN SERVER
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)