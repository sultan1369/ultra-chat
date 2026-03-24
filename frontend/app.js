const API = "https://ultra-chat-backend-4ka5.onrender.com";

let lastId = 0;

// 🔔 Request notification permission
if (Notification.permission !== "granted") {
  Notification.requestPermission();
}

// 🔊 Notify
function notify(msg) {
  const currentUser = document.getElementById("user").value;

  if (msg[1] !== currentUser) {
    document.getElementById("ping").play();

    if (Notification.permission === "granted") {
      new Notification("New Message", {
        body: msg[2]
      });
    }
  }
}

// 📤 SEND
function send() {
  const user = document.getElementById("user").value;
  const msg = document.getElementById("msg").value;

  if (!msg) return;

  const receiver = user === "S" ? "F" : "S";

  fetch(API + "/s", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      s: user,
      r: receiver,
      m: msg.slice(0, 50),
      t: Math.floor(Date.now()/1000)
    })
  });

  document.getElementById("msg").value = "";
}

// 📥 FETCH ONLY NEW MESSAGES
function fetchMessages() {
  const user = document.getElementById("user").value;

  fetch(`${API}/r/${user}/${lastId}`)
    .then(res => res.ok ? res.json() : [])
    .then(data => {
      data.forEach(msg => {
        lastId = msg[0];
        renderOne(msg);
        notify(msg);
      });
    })
    .catch(() => {});
}

// 🧱 RENDER SINGLE MESSAGE
function renderOne(item) {
  const chat = document.getElementById("chat");
  const div = document.createElement("div");

  div.classList.add("msg");

  const currentUser = document.getElementById("user").value;

  if (item[1] === currentUser) {
    div.classList.add("s");
  } else {
    div.classList.add("f");
  }

  const text = document.createElement("div");
  text.innerText = item[2];

  const time = document.createElement("div");
  time.classList.add("time");

  time.innerText = new Date(item[3]*1000)
    .toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});

  div.appendChild(text);
  div.appendChild(time);

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// 🔁 SMART POLLING (LOW NETWORK)
setInterval(fetchMessages, 5000);