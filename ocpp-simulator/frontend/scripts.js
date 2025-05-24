const base = "http://localhost:8000";

function connect() {
  fetch(`${base}/connect`).then(res => res.json()).then(console.log);
}
function disconnect() {
  fetch(`${base}/disconnect`).then(res => res.json()).then(console.log);
}
function status(s) {
  fetch(`${base}/status/${s}`, { method: "POST" }).then(res => res.json()).then(console.log);
}
