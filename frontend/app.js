const API = "https://ultra-chat-backend-4ka5.onrender.com";

// 🔄 STATE
let lastId = 0;
let interval = 5000;
let queue = [];
let isHidden = false;
let isInitialLoad = true;

// 🔔 PERMISSION + AUDIO UNLOCK
document.body.addEventListener("click", () => {
  if ("Notification" in window && Notification.permission !== "granted") {
    Notification.requestPermission();
  }

  const audio = document.getElementById("ping");
  if (audio) {
    audio.play().then(() => audio.pause()).catch(() => {});
  }
}, { once: true });

// 🔥 SERVICE WORKER
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js");
}

// 🔍 BACKGROUND STATE
document.addEventListener("visibilitychange", () => {
  isHidden = document.hidden;
});

// 🔔 NOTIFICATION
function notifySW() {
  if (navigator.serviceWorker && Notification.permission === "granted") {
    navigator.serviceWorker.ready.then(reg => {
      reg.showNotification("New Message", {
        body: "You have a new message",
        tag: "msg",
        renotify: true,
        vibrate: [200, 100, 200]
      });
    });
  }
}

// 🔊 SOUND
function playSound() {
  const audio = document.getElementById("ping");
  if (audio) audio.play().catch(() => {});
}

// 📤 SEND MESSAGE (WITH STATUS)
function send() {
  const user = document.getElementById("user").value;
  const msgInput = document.getElementById("msg");
  const msg = msgInput.value.trim();

  if (!msg) return;

  const timestamp = Math.floor(Date.now() / 1000);
  const id = "local_" + Date.now(); // local ID

  const data = {
    id: id,
    s: user,
    r: user === "S" ? "F" : "S",
    m: msg.slice(0, 40),
    t: timestamp
  };

  // 🔥 render instantly
  renderLocal(data);

  queue.push(data);
  msgInput.value = "";

  trySendQueue();
}

// 🔁 SEND QUEUE
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
      updateStatus(item.id, "✓"); // sent
      queue.shift();
      trySendQueue();
    }
  })
  .catch(() => {});
}

// 📥 FETCH
function fetchMessages() {
  const user = document.getElementById("user").value;
  const startId = isInitialLoad ? -1 : lastId;

  fetch(`${API}/r/${user}/${startId}`)
    .then(res => res.ok ? res.json() : [])
    .then(data => {

      if (isInitialLoad) {
        document.getElementById("chat").innerHTML = "";
        isInitialLoad = false;
      }

      data.forEach(m => {
        lastId = m[0];

        // avoid duplicate local messages
        if (!document.getElementById("msg_" + m[0])) {
          renderServer(m);
        }

        if (m[1] !== user) {
          playSound();
          if (isHidden) notifySW();
        }
      });

      interval = data.length > 0 ? 3000 : 8000;

      trySendQueue();

      setTimeout(fetchMessages, interval);
    })
    .catch(() => setTimeout(fetchMessages, 10000));
}

// 🧱 LOCAL RENDER (SENDING)
function renderLocal(m) {
  const chat = document.getElementById("chat");

  const div = document.createElement("div");
  div.className = "msg s";
  div.id = m.id;

  div.innerHTML = `
    ${m.m}
    <div class="time">
      ${new Date(m.t * 1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}
      <span class="status">⏳</span>
    </div>
  `;

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// 🧱 SERVER RENDER
function renderServer(m) {
  const chat = document.getElementById("chat");
  const current = document.getElementById("user").value;

  const div = document.createElement("div");
  div.className = "msg " + (m[1] === current ? "s" : "f");
  div.id = "msg_" + m[0];

  div.innerHTML = `
    ${m[2]}
    <div class="time">
      ${new Date(m[3]*1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}
    </div>
  `;

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// 🔄 UPDATE STATUS
function updateStatus(id, status) {
  const el = document.getElementById(id);
  if (el) {
    const span = el.querySelector(".status");
    if (span) span.innerText = status;
  }
}

// 🔄 USER SWITCH
document.getElementById("user").addEventListener("change", () => {
  lastId = 0;
  isInitialLoad = true;
  document.getElementById("chat").innerHTML = "";
});

// 📶 NETWORK RECOVERY
window.addEventListener("online", trySendQueue);

// 🚀 START
fetchMessages();
