"""Cross-laptop network synchronization for AutoTyper.

Provides:
- Embedded HTTP sync server on Laptop 2 (Receiver)
- Zero-install Web Dashboard for Laptop 1 (Sender)
- REST API for text sync, speed controls, and status monitoring
- File watcher and CLI pusher for Laptop 1
"""

import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from . import config


def get_lan_ip():
    """Discover the machine's primary local LAN IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def get_dashboard_html():
    """Return self-contained, offline-compatible modern web dashboard."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AutoTyper Sync Dashboard</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem 1rem 3rem 1rem;
    }
    .container {
      width: 100%;
      max-width: 860px;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1rem;
    }
    .brand h1 {
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .brand p {
      font-size: 0.85rem;
      color: var(--muted);
      margin-top: 0.2rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      background: #334155;
      color: #e2e8f0;
      letter-spacing: 0.03em;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #94a3b8;
    }
    .badge.RUNNING { background: #064e3b; color: #6ee7b7; }
    .badge.RUNNING .dot { background: var(--success); box-shadow: 0 0 8px var(--success); }
    .badge.PAUSED { background: #78350f; color: #fde68a; }
    .badge.PAUSED .dot { background: var(--warning); }
    .badge.COUNTDOWN { background: #1e3a8a; color: #93c5fd; }
    .badge.COUNTDOWN .dot { background: var(--primary); }
    .badge.STOPPED { background: #334155; color: #cbd5e1; }
    .badge.STOPPED .dot { background: #94a3b8; }

    .stats-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.85rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      font-size: 0.85rem;
    }
    .stat-item {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .stat-label {
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .stat-value {
      font-weight: 600;
      font-family: var(--font-mono);
    }

    .editor-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .editor-header {
      background: #172033;
      padding: 0.65rem 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      font-size: 0.85rem;
      color: var(--muted);
    }
    textarea {
      width: 100%;
      min-height: 340px;
      padding: 1rem;
      background: transparent;
      color: #f1f5f9;
      font-family: var(--font-mono);
      font-size: 0.95rem;
      line-height: 1.5;
      border: none;
      resize: vertical;
      outline: none;
      white-space: pre;
    }
    .editor-footer {
      background: #172033;
      padding: 0.75rem 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
      border-top: 1px solid var(--border);
    }
    .auto-sync-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
      color: var(--muted);
      cursor: pointer;
      user-select: none;
    }
    .auto-sync-label input {
      accent-color: var(--primary);
    }
    .btn-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    button, select {
      padding: 0.55rem 1.1rem;
      border-radius: 6px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.15s ease-in-out;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    select {
      background: #172033;
      color: #f8fafc;
      border: 1px solid var(--border);
      padding: 0.45rem 0.8rem;
    }
    .btn-primary {
      background: var(--primary);
      color: #0f172a;
    }
    .btn-primary:hover {
      background: var(--primary-hover);
      color: #ffffff;
    }
    .btn-secondary {
      background: #334155;
      color: #e2e8f0;
    }
    .btn-secondary:hover {
      background: #475569;
    }
    .btn-danger {
      background: #991b1b;
      color: #fecaca;
    }
    .btn-danger:hover {
      background: var(--danger);
      color: #ffffff;
    }
    .controls-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }
    .controls-title {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .settings-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 1.25rem;
      padding: 0.4rem 0;
      border-bottom: 1px solid #293548;
    }
    .setting-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
    }
    .controls-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
    }
    .hint {
      font-size: 0.8rem;
      color: var(--muted);
      line-height: 1.4;
    }
    .banner {
      padding: 0.6rem 1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 500;
      display: none;
      align-items: center;
      gap: 0.5rem;
    }
    .banner.show { display: flex; }
    .banner.success { background: #064e3b; color: #a7f3d0; border: 1px solid #059669; }
    .banner.error { background: #7f1d1d; color: #fecaca; border: 1px solid #dc2626; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <h1>⌨️ AutoTyper Remote Sync</h1>
        <p>Type here on Laptop 1 &mdash; Laptop 2 will type it out when triggered.</p>
      </div>
      <div>
        <span id="statusBadge" class="badge STOPPED">
          <span class="dot"></span>
          <span id="statusText">STOPPED</span>
        </span>
      </div>
    </header>

    <div class="stats-card">
      <div class="stat-item">
        <span class="stat-label">Progress</span>
        <span id="statProgress" class="stat-value">0 / 0 chars (0%)</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Current Speed</span>
        <span id="statSpeed" class="stat-value">~65 chars/s</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Receiver File</span>
        <span id="statFile" class="stat-value" style="font-size: 0.8rem;">~/autotype_text.txt</span>
      </div>
    </div>

    <div id="banner" class="banner"></div>

    <div class="editor-card">
      <div class="editor-header">
        <span>Source Code / Text</span>
        <span id="charCount">0 characters &bull; 0 lines</span>
      </div>
      <textarea id="editor" placeholder="Type or paste code here... Laptop 2 will receive it instantly." spellcheck="false"></textarea>
      <div class="editor-footer">
        <label class="auto-sync-label">
          <input type="checkbox" id="autoSync" checked>
          <span>Auto-sync while typing (0.8s debounce)</span>
        </label>
        <div class="btn-group">
          <button id="btnFetch" class="btn-secondary" title="Fetch current text stored on Laptop 2">🔄 Reload from Laptop 2</button>
          <button id="btnSync" class="btn-primary">🚀 Sync to Laptop 2</button>
        </div>
      </div>
    </div>

    <div class="controls-card">
      <div class="controls-title">Settings & Tuning</div>
      <div class="settings-row">
        <div class="setting-group">
          <label for="speedPreset" style="color: var(--muted);">Typing Speed:</label>
          <select id="speedPreset">
            <option value="0.015" selected>⚡ Reliable (~65 chars/s) [Recommended]</option>
            <option value="0.010">🚀 Fast (~100 chars/s)</option>
            <option value="0.003">🏎️ Turbo (~300 chars/s)</option>
            <option value="0.050">🐢 Human (~20 chars/s)</option>
          </select>
        </div>
        <div class="setting-group">
          <label class="auto-sync-label" title="Keep OFF for browser editors and tests to prevent deleted lines">
            <input type="checkbox" id="smartIndent">
            <span>Strip IDE auto-indent (Keep OFF for web/browser editors)</span>
          </label>
        </div>
      </div>

      <div class="controls-title" style="margin-top: 0.25rem;">Remote Controls</div>
      <div class="controls-row">
        <button id="btnToggle" class="btn-secondary">⏯️ Toggle Start / Pause</button>
        <button id="btnStop" class="btn-danger">⏹️ Emergency Stop</button>
        <button id="btnSlower" class="btn-secondary">🐢 Slower</button>
        <button id="btnFaster" class="btn-secondary">⚡ Faster</button>
      </div>
      <p class="hint">
        💡 <strong>Pro-Tip:</strong> The person on Laptop 2 can start, pause, or resume anytime by pressing <strong>F8</strong> or <strong>Ctrl + Alt + Space</strong> directly on their physical keyboard!
      </p>
    </div>
  </div>

  <script>
    const editor = document.getElementById("editor");
    const charCount = document.getElementById("charCount");
    const btnSync = document.getElementById("btnSync");
    const btnFetch = document.getElementById("btnFetch");
    const btnToggle = document.getElementById("btnToggle");
    const btnStop = document.getElementById("btnStop");
    const btnSlower = document.getElementById("btnSlower");
    const btnFaster = document.getElementById("btnFaster");
    const speedPreset = document.getElementById("speedPreset");
    const smartIndent = document.getElementById("smartIndent");
    const autoSync = document.getElementById("autoSync");
    const statusBadge = document.getElementById("statusBadge");
    const statusText = document.getElementById("statusText");
    const statProgress = document.getElementById("statProgress");
    const statSpeed = document.getElementById("statSpeed");
    const statFile = document.getElementById("statFile");
    const banner = document.getElementById("banner");

    let debounceTimer = null;
    let isUserTyping = false;

    function updateCounts() {
      const text = editor.value;
      const chars = text.length;
      const lines = text ? text.split("\\n").length : 0;
      charCount.textContent = `${chars} characters • ${lines} lines`;
    }

    editor.addEventListener("keydown", function(e) {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
        updateCounts();
      }
    });

    editor.addEventListener("input", () => {
      isUserTyping = true;
      updateCounts();
      if (autoSync.checked) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          sendText(false);
          isUserTyping = false;
        }, 800);
      }
    });

    function showBanner(msg, type = "success") {
      banner.textContent = msg;
      banner.className = `banner show ${type}`;
      setTimeout(() => {
        banner.className = "banner";
      }, 3500);
    }

    async function sendText(showSuccessBanner = true) {
      const text = editor.value;
      try {
        const res = await fetch("/api/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text })
        });
        const data = await res.json();
        if (showSuccessBanner) {
          showBanner(`✅ Synced ${data.chars} characters (${data.lines} lines) to Laptop 2!`, "success");
        }
      } catch (err) {
        showBanner("❌ Failed to sync: " + err.message, "error");
      }
    }

    async function fetchInitialText() {
      try {
        const res = await fetch("/api/text");
        const data = await res.json();
        if (data.text !== undefined && (!isUserTyping || !editor.value)) {
          editor.value = data.text;
          updateCounts();
        }
      } catch (err) {
        console.error("Could not fetch text:", err);
      }
    }

    async function sendAction(action, payload = {}) {
      try {
        const bodyObj = Object.assign({ action: action }, payload);
        const res = await fetch("/api/action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(bodyObj)
        });
        const data = await res.json();
        if (data.status_info) {
          applyStatus(data.status_info);
        }
      } catch (err) {
        showBanner("❌ Action failed: " + err.message, "error");
      }
    }

    speedPreset.addEventListener("change", () => {
      const val = parseFloat(speedPreset.value);
      sendAction("set_delay", { delay: val });
      showBanner(`⚡ Speed updated to ~${Math.round(1/val)} chars/sec`, "success");
    });

    smartIndent.addEventListener("change", () => {
      const val = smartIndent.checked;
      sendAction("set_smart_indent", { enabled: val });
      showBanner(`Indent cleanup ${val ? "Enabled" : "Disabled (Safe)"}`, "success");
    });

    function applyStatus(info) {
      statusBadge.className = `badge ${info.state || "STOPPED"}`;
      statusText.textContent = info.state || "STOPPED";
      statProgress.textContent = `${info.index || 0} / ${info.total || 0} chars (${info.progress_percent || 0}%)`;
      statSpeed.textContent = `~${info.chars_per_sec || 0} chars/s (${info.delay}s)`;
      if (info.file_path) {
        statFile.textContent = info.file_path;
      }
      if (info.smart_indent !== undefined) {
        smartIndent.checked = Boolean(info.smart_indent);
      }
    }

    async function pollStatus() {
      try {
        const res = await fetch("/api/status");
        if (res.ok) {
          const info = await res.json();
          applyStatus(info);
        }
      } catch (err) {
        statusBadge.className = "badge STOPPED";
        statusText.textContent = "OFFLINE";
      }
    }

    btnSync.addEventListener("click", () => sendText(true));
    btnFetch.addEventListener("click", () => {
      fetchInitialText();
      showBanner("🔄 Reloaded current text from Laptop 2", "success");
    });
    btnToggle.addEventListener("click", () => sendAction("toggle"));
    btnStop.addEventListener("click", () => sendAction("cancel"));
    btnSlower.addEventListener("click", () => sendAction("slower"));
    btnFaster.addEventListener("click", () => sendAction("faster"));

    fetchInitialText();
    pollStatus();
    setInterval(pollStatus, 1000);
  </script>
</body>
</html>"""


class SyncHandler(BaseHTTPRequestHandler):
    """HTTP request handler for AutoTyper sync."""

    typer = None

    def _set_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200, "text/plain")
        self.wfile.write(b"OK")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("", "/index.html"):
            html = get_dashboard_html().encode("utf-8")
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(html)
            return

        if path == "/api/status":
            if self.typer is not None:
                info = self.typer.get_status()
            else:
                info = {"state": "STOPPED", "index": 0, "total": 0, "delay": config.CHAR_DELAY}
            payload = json.dumps(info).encode("utf-8")
            self._set_headers(200)
            self.wfile.write(payload)
            return

        if path == "/api/text":
            text = self.typer.text if self.typer else ""
            payload = json.dumps({"text": text, "chars": len(text)}).encode("utf-8")
            self._set_headers(200)
            self.wfile.write(payload)
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
        except Exception:
            body = b""

        if path == "/api/text":
            text = ""
            content_type = self.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    data = json.loads(body.decode("utf-8", errors="replace"))
                    text = data.get("text", "")
                except Exception:
                    text = body.decode("utf-8", errors="replace")
            else:
                text = body.decode("utf-8", errors="replace")

            if self.typer:
                total = self.typer.update_text(text, save_file=True)
                lines = len(text.splitlines()) if text else 0
            else:
                total, lines = 0, 0

            response = json.dumps({"status": "ok", "chars": total, "lines": lines}).encode("utf-8")
            self._set_headers(200)
            self.wfile.write(response)
            return

        if path == "/api/action":
            action = ""
            data = {}
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
                action = data.get("action", "").lower()
            except Exception:
                pass

            if self.typer:
                if action == "toggle":
                    self.typer.toggle()
                elif action in ("cancel", "stop"):
                    self.typer.cancel()
                elif action == "slower":
                    self.typer.adjust_delay(+0.01)
                elif action == "faster":
                    self.typer.adjust_delay(-0.01)
                elif action == "set_delay":
                    delay_val = float(data.get("delay", config.CHAR_DELAY))
                    self.typer.set_delay(delay_val)
                elif action == "set_smart_indent":
                    config.SMART_INDENT = bool(data.get("enabled", False))

            info = self.typer.get_status() if self.typer else {}
            response = json.dumps({"status": "ok", "action": action, "status_info": info}).encode("utf-8")
            self._set_headers(200)
            self.wfile.write(response)
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def log_message(self, format, *args):
        if args and len(args) > 0 and str(args[0]).startswith("GET /api/status"):
            return
        super().log_message(format, *args)


class ThreadedSyncServer(HTTPServer):
    daemon_threads = True


def start_sync_server(typer, host="0.0.0.0", port=8765):
    SyncHandler.typer = typer
    server = ThreadedSyncServer((host, port), SyncHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    lan_ip = get_lan_ip()
    return server, lan_ip, port


# ---------------------------------------------------------------------------
# Client functions for Laptop 1 (Sender)
# ---------------------------------------------------------------------------

def normalize_server_url(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return url.rstrip("/")


def send_text(server_url, text, timeout=5):
    base_url = normalize_server_url(server_url)
    endpoint = f"{base_url}/api/text"
    payload = json.dumps({"text": text}).encode("utf-8")

    req = Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def send_file(server_url, file_path, timeout=5):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return send_text(server_url, content, timeout=timeout)


def watch_file(server_url, file_path, interval=0.5):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    base_url = normalize_server_url(server_url)
    print("=" * 60)
    print("AutoTyper File Watcher Active (Sender Mode)")
    print("=" * 60)
    print(f"Watching local file : {os.path.abspath(file_path)}")
    print(f"Target Sync Server  : {base_url}")
    print("Whenever you save this file, it will sync to Laptop 2 instantly!")
    print("Press Ctrl+C to stop watching.\n")

    last_mtime = None
    last_content = None

    while True:
        try:
            current_mtime = os.path.getmtime(file_path)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content != last_content:
                    last_content = content
                    try:
                        res = send_text(base_url, content)
                        chars = res.get("chars", len(content))
                        lines = res.get("lines", len(content.splitlines()))
                        t_str = time.strftime("%H:%M:%S")
                        print(f"[{t_str}] Synced {chars} chars ({lines} lines) to {base_url}")
                    except URLError as e:
                        print(f"[{time.strftime('%H:%M:%S')}] Connection error: {e}")
                    except Exception as e:
                        print(f"[{time.strftime('%H:%M:%S')}] Sync error: {e}")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped file watcher.")
            break
