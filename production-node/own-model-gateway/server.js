"use strict";

const http = require("http");

const PORT = Number(process.env.OWN_MODEL_GATEWAY_PORT || 9010);
const UPSTREAM = String(process.env.OWN_MODEL_UPSTREAM || "http://127.0.0.1:9000");

function proxyJson(req, res, path) {
  const chunks = [];
  req.on("data", (d) => chunks.push(d));
  req.on("end", async () => {
    const body = Buffer.concat(chunks);
    try {
      const r = await fetch(UPSTREAM + path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
      });
      const txt = await r.text();
      res.writeHead(r.status, { "content-type": r.headers.get("content-type") || "application/json" });
      res.end(txt);
    } catch (e) {
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ detail: "Own model upstream unavailable.", error: String(e && e.message || e) }));
    }
  });
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true, gateway: "own-model-gateway", upstream: UPSTREAM }));
    return;
  }
  if (req.method === "POST" && req.url === "/v1/chat/completions") {
    proxyJson(req, res, "/v1/chat/completions");
    return;
  }
  if (req.method === "POST" && req.url === "/v1/chat/completions/stream") {
    proxyJson(req, res, "/v1/chat/completions/stream");
    return;
  }
  res.writeHead(404, { "content-type": "application/json" });
  res.end(JSON.stringify({ detail: "Not found" }));
});

server.listen(PORT, () => {
  console.log(`[own-model-gateway] listening on :${PORT}, upstream=${UPSTREAM}`);
});
