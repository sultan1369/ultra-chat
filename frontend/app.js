const API = "https://ultra-chat-backend-4ka5.onrender.com";

// 🔄 STATE
let lastId = 0;
let interval = 5000;
let queue = []; // offline queue

// 🔔 REQUEST NOTIFICATION PERMISSION
if ("Notification" in window && Notification.permission !== "granted") {
  Notification.requestPermission();
}

// 🔥 REGISTER SERVICE WORKER (PWA)
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js");
}

// 🔔 PRIVACY NOTIFICATION (no message content)
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

// 📤 SEND MESSAGE (WITH OFFLINE SUPPORT)
function send() {
  const user = document.getElementById("user").value;
  const msgInput = document.getElementById("msg");
  const msg = msgInput.value.trim();

  if (!msg) return;

  const data = {
    s: user,
    r: user === "S" ? "F" : "S",
    m: msg.slice(0, 40), // ultra small payload
    t: Math.floor(Date.now() / 1000)
  };

  // add to queue
  queue.push(data);

  msgInput.value = "";

  // try send immediately
  trySendQueue();
}

// 🔁 TRY SEND QUEUE (LOW NETWORK SAFE)
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
      queue.shift(); // remove sent message
      trySendQueue(); // send next
    }
  })
  .catch(() => {
    // keep in queue, retry later
  });
}

// 📥 FETCH ONLY NEW MESSAGES (ADAPTIVE)
function fetchMessages() {
  const user = document.getElementById("user").value;

  fetch(`${API}/r/${user}/${lastId}`)
    .then(res => res.ok ? res.json() : [])
    .then(data => {

      if (data.length > 0) {
        playSound();
        notify();
        interval = 3000; // faster when active
      } else {
        interval = 8000; // slower when idle
      }

      data.forEach(m => {
        lastId = m[0];
        render(m);
      });

      // retry sending queued messages
      trySendQueue();

      setTimeout(fetchMessages, interval);
    })
    .catch(() => {
      // network weak → retry slowly
      setTimeout(fetchMessages, 10000);
    });
}

// 🧱 RENDER MESSAGE (LEFT/RIGHT LOGIC)
function render(m) {
  const chat = document.getElementById("chat");
  const current = document.getElementById("user").value;

  const div = document.createElement("div");
  div.className = "msg " + (m[1] === current ? "s" : "f");

  const text = document.createElement("div");
  text.innerText = m[2];

  const time = document.createElement("div");
  time.className = "time";
  time.innerText = new Date(m[3] * 1000)
    .toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });

  div.appendChild(text);
  div.appendChild(time);

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// 📶 NETWORK CHANGE HANDLING
window.addEventListener("online", trySendQueue);

// 🔄 START SYSTEM
fetchMessages();