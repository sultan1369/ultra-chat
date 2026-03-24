const API = "http://192.168.31.71:8000";

// SEND MESSAGE
function send() {
  const user = document.getElementById("user").value;
  const msg = document.getElementById("msg").value;

  if (!msg) return;

  const receiver = user === "S" ? "F" : "S";

  fetch(API + "/s", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      s: user,
      r: receiver,
      m: msg,
      t: Math.floor(Date.now() / 1000) // 🔥 timestamp
    })
  });

  document.getElementById("msg").value = "";
}


// 🔥 POLLING (every 1 sec)
setInterval(() => {
  const user = document.getElementById("user").value;

  fetch(API + "/r/" + user)
    .then(res => res.json())
    .then(data => {
      console.log("DATA:", data);   // 🔥 DEBUG
      render(data);
    })
    .catch(err => console.error(err));
}, 1000);


// RENDER CHAT
function render(data) {
  const chat = document.getElementById("chat");
  chat.innerHTML = "";

  const currentUser = document.getElementById("user").value;

  data.forEach(item => {
    const msgBox = document.createElement("div");
    msgBox.classList.add("msg");

    if (item[0] === currentUser) {
      msgBox.classList.add("s");
    } else {
      msgBox.classList.add("f");
    }

    const text = document.createElement("div");
    text.classList.add("text");
    text.innerText = item[1];

    const time = document.createElement("div");
    time.classList.add("time");

    time.innerText = new Date(item[2] * 1000)
  .toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

    msgBox.appendChild(text);
    msgBox.appendChild(time);

    chat.appendChild(msgBox);
  });

  chat.scrollTop = chat.scrollHeight;
}