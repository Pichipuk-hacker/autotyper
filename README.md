# Windows AutoTyper & Cross-Device Sync

A high-speed, remote-compatible Python Auto-Typer with **Cross-Laptop Synchronization** that works across **the same Wi-Fi, different Wi-Fi networks, mobile hotspots, or anywhere in the world**.

It simulates real Windows Virtual Keys (`wVk`) + Hardware Scan Codes (`wScan`) via Win32 `SendInput`, bypassing clipboard blocks and paste monitors in proctored tests, browser IDEs, and remote desktops.

---

## 🚀 How to Use Between Two Laptops

### Step 1: Start on Laptop 2 (Receiver / Target Window)
Double-click **`Start_AutoTyper.bat`**. The terminal opens and displays:

```text
============================================================
AutoTyper Active & Listening (Dual Network: Local + Internet)
============================================================
Reading from        : C:\Users\Username\autotype_text.txt
Local Wi-Fi URL     : http://192.168.1.45:8765 (If both laptops are on same Wi-Fi)
Internet Cloud Room : https://ntfy.sh/autotyper-pichipuk-sync (If on DIFFERENT Wi-Fi / anywhere!)
Indentation Mode    : SMART (Fixes HackerRank / LeetCode / Monaco Portals)
------------------------------------------------------------
Hotkeys (Physical Keyboard on Laptop 2):
  - F8 or Ctrl + Alt + Space : Toggle (Start / Pause / Resume)
  - F9 or Ctrl + Alt + I     : Toggle Indent Fix (SMART: portals / RAW: notepad)
  - Escape or Ctrl + Alt + C : Emergency Stop / Cancel
  - Alt + = / Alt + -        : Slower / Faster
============================================================
```

---

### Step 2: Send Code from Laptop 1 (Sender)

#### If Laptops are on DIFFERENT Wi-Fi / Hotspot / Anywhere in the World:
* **Option A (Universal Dashboard — Recommended):**
  Double-click **`dashboard.html`** on Laptop 1 in Chrome/Edge.
  Paste your code, select Indentation Mode (Smart Fix is default), and click **`🚀 Send to Laptop 2`**.
  Laptop 2 plays a chime and loads the code instantly!
* **Option B (Desktop 1-Click):**
  Double-click **`Send_Code_Laptop1.bat`** on Laptop 1.
  It opens Notepad. Paste your code, press `Ctrl + S`, close Notepad, and it immediately sends to Laptop 2!
* **Option C (Live File Watcher in VS Code / Notepad):**
  ```powershell
  python autotyper.py watch "code.txt" --room autotyper-pichipuk-sync
  ```
  Every time you press `Ctrl + S` on Laptop 1, it automatically syncs to Laptop 2 over the internet!
* **Option D (Direct Web Browser):**
  Open the Cloud Room in any browser on Laptop 1 (or mobile phone):
  👉 **`https://ntfy.sh/autotyper-pichipuk-sync`**

#### If Laptops are on the SAME Wi-Fi:
* Open the Local URL (e.g. `http://192.168.1.45:8765`) in any browser on Laptop 1.

---

### Step 3: Trigger on Laptop 2
1. Click the mouse into the target text box or code editor.
2. Press **`F8`** or **`Ctrl + Alt + Space`**.
3. AutoTyper counts down 5 seconds, then types the code character-by-character with 100% accurate indentation!

| Hotkey on Laptop 2 | Action |
| :--- | :--- |
| **`F8`** or **`Ctrl + Alt + Space`** | **Start** typing |
| **`F8`** or **`Ctrl + Alt + Space`** *(while typing)* | **Pause** typing instantly |
| **`F8`** or **`Ctrl + Alt + Space`** *(while paused)* | **Resume** typing right where it stopped |
| **`F9`** or **`Ctrl + Alt + I`** | **Toggle Indent Fix** (SMART: portals / RAW: notepad) |
| **`Esc`** or **`Ctrl + Alt + C`** | **Cancel / Stop** & reset to beginning |
| **`Alt + =`** / **`Alt + -`** | Adjust speed slower or faster |

---

## 🔄 1-Click Auto-Updater (Never Download ZIPs Manually Again)

Whenever updates are pushed to GitHub, you **do not need to download ZIP files manually**.
Simply double-click:
👉 **`Update_AutoTyper.bat`**

It automatically fetches and updates all files directly from GitHub in 3 seconds!

---

## Code Structure

```text
autotyper/
├── config.py       # Constants, speed presets, indent modes & cloud room names
├── engine.py       # AutoTyper state machine, typing engine & safe indent handler
├── hotkeys.py      # Global hotkey listener (F8, F9, Ctrl+Alt+Space, Esc)
├── sync.py         # HTTP sync server, Cloud Room (ntfy.sh) client, and REST API
├── win32_input.py  # Win32 SendInput, VirtualKey & hardware scan-code mappings
├── cli.py          # Command line runner (run, send, watch, stop)
├── selftest.py     # Built-in self-test suite
├── notify.py       # Notification hook
└── pid.py          # Single-instance process lock

dashboard.html      # Standalone sender dashboard with Indent Fix toggle for Laptop 1
Send_Code_Laptop1.bat# 1-Click desktop sender for Laptop 1
Start_AutoTyper.bat # Self-installing launcher for Laptop 2
Update_AutoTyper.bat# 1-Click auto-updater from GitHub
Setup_Laptop2.bat   # Standalone 1-click dependency installer
```
