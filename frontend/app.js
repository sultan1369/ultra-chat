const API = "https://ultra-chat-backend-4ka5.onrender.com";

// 🔄 STATE
let lastId = 0;
let interval = 3000;
let queue = [];

// 🔔 REQUEST NOTIFICATION PERMISSION (ON USER CLICK)
document.body.addEventListener("click", () => {
  if ("Notification" in window && Notification.permission !== "granted") {
    Notification.requestPermission();
  }

  // 🔊 unlock audio (important for mobile)
  const audio = document.getElementById("ping");
  if (audio) {
    audio.play().then(() => audio.pause()).catch(() => {});
  }
}, { once: true });

// 🔥 REGISTER SERVICE WORKER
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js");
}

// 🔔 PRIVACY NOTIFICATION
function notify() {
  if (Notification.permission === "granted") {
    new Notification("New Message");
  }
}

// 🔊 SOUND
function playSound() {
  const audio = document.getElementById("ping");
  if (audio) audio.play().catch(() => {});
}

// 📤 SEND MESSAGE (WITH OFFLINE QUEUE)
function send() {
  const user = document.getElementById("user").value;
  const msgInput = document.getElementById("msg");
  const msg = msgInput.value.trim();

  if (!msg) return;

  const data = {
    s: user,
    r: user === "S" ? "F" : "S",
    m: msg.slice(0, 40),
    t: Math.floor(Date.now() / 1000)
  };

  // add to queue
  queue.push(data);

  msgInput.value = "";

  trySendQueue();
}

// 🔁 SEND QUEUE (LOW NETWORK SAFE)
function trySendQueue() {
  if (!navigator.onLine || queue.length === 0) return;

  const item = queue[0];

  fetch(API + "/s", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(item)
  })
  .then(res => {
    if (res.ok) {
      queue.shift();
      trySendQueue();
    }
  })
  .catch(() => {});
}

// 📥 FETCH MESSAGES (FIXED INITIAL LOAD)
function fetchMessages() {
  const user = document.getElementById("user").value;

  const startId = lastId === 0 ? -1 : lastId;

  fetch(`${API}/r/${user}/${startId}`)
    .then(res => res.ok ? res.json() : [])
    .then(data => {

      data.forEach(m => {
        lastId = m[0];
        render(m);

        // 🔔 notify only if message from other user
        if (m[1] !== user) {
          playSound();
          notify();
        }
      });

      // 🔄 adaptive polling
      interval = data.length > 0 ? 3000 : 8000;

      trySendQueue();

      setTimeout(fetchMessages, interval);
    })
    .catch(() => {
      setTimeout(fetchMessages, 10000);
    });
}

// 🧱 RENDER MESSAGE (LEFT/RIGHT)
function render(m) {
  const chat = document.getElementById("chat");
  const current = document.getElementById("user").value;

  const div = document.createElement("div");
  div.className = "msg " + (m[1] === current ? "s" : "f");

  const text = document.createElement("div");
  text.innerText = m[2];

  const time = document.createElement("div");
  time.className = "time";
  time.innerText = new Date(m[3] * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  div.appendChild(text);
  div.appendChild(time);

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// 🔄 RESET WHEN USER CHANGES
document.getElementById("user").addEventListener("change", () => {
  lastId = 0;
  document.getElementById("chat").innerHTML = "";
});

// 📶 NETWORK RECOVERY
window.addEventListener("online", trySendQueue);

// 🚀 START APP
fetchMessages();