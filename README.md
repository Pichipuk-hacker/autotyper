# Windows AutoTyper & Built-in Keyboard Lock (`AutoHotInterception`)

This repository contains tools for Windows:
1. **AutoTyper** — A high-speed (1,000 chars/sec), remote-compatible Python Auto-Typer that reads text dynamically from `~/autotype_text.txt` (or over the network) and sends real Win32 Virtual Keys (`wVk`) + Hardware Scan Codes (`wScan`). Works locally, across remote desktops (AnyDesk, Parsec, GlideX, RDP), and supports **Cross-Laptop Synchronization**.
2. **Cross-Laptop Sync Engine** — Type or paste code on **Laptop 1** (via a zero-install browser dashboard or file watcher), and have the person on **Laptop 2** trigger, pause, resume, and stop the typing into their active window whenever they want using custom hotkeys (`F8`, `Ctrl + Alt + Space`).
3. **`HP_Keyboard_Lock.ahk`** — An AutoHotkey v2 + AutoHotInterception script that blocks selected keys (`A–Z`, `0–9`, symbols) **only on the laptop's built-in keyboard** while keeping external USB/Bluetooth keyboards 100% functional.

---

## Part 1: Cross-Laptop Setup (Type on Laptop 1 -> AutoType on Laptop 2)

This mode allows you to write or edit code on **Laptop 1** while another person on **Laptop 2** automatically receives the text and types it into any target window on demand using keyboard shortcuts.

### Step 1: Start AutoTyper on Laptop 2 (Receiver)
On **Laptop 2** (where the target application/window is):
1. Double-click **`Start_AutoTyper.bat`** (or run `python autotyper.py`).
2. The terminal will start the listener and display the **Web Dashboard URL**, for example:
   ```text
   ============================================================
   AutoTyper Active & Listening (Windows + Remote Keyboard)
   ============================================================
   Reading from   : C:\Users\Username\autotype_text.txt
   Sync Server    : Active on port 8765
   Web Dashboard  : http://192.168.1.45:8765 (Open this on Laptop 1 or phone!)
   Local URL      : http://localhost:8765
   ------------------------------------------------------------
   Hotkeys (Physical Keyboard on this Laptop):
     - Ctrl + Alt + Space : Toggle (Start / Pause / Resume) [Recommended]
     - F8                 : Toggle Alternative
     - Escape / Ctrl+Alt+C: Emergency Stop / Cancel
     - Alt + = / Alt + -  : Slower / Faster
   ============================================================
   ```
*(Make sure both laptops are on the same Wi-Fi / local network, or connected via mobile hotspot).*

---

### Step 2: Send Text from Laptop 1 (Sender)

You have **two options** on Laptop 1:

#### Option A: Web Dashboard (Zero Installation — Recommended)
1. Open any web browser on **Laptop 1** (Chrome, Edge, Firefox, Safari, or even a smartphone).
2. Enter the URL shown on Laptop 2 (e.g. `http://192.168.1.45:8765`).
3. Type or paste your code into the editor.
4. Click **🚀 Sync to Laptop 2** (or keep **Auto-sync while typing** checked to sync automatically as you write).
5. The dashboard shows real-time progress, typing speed, and status (`STOPPED`, `COUNTDOWN`, `RUNNING`, `PAUSED`).

#### Option B: Automatic File Watcher (Edit in VS Code / Notepad)
If you prefer typing in your own code editor (VS Code, Notepad, Sublime) on Laptop 1:
```powershell
python autotyper.py watch "C:\path\to\my_code.py" --server http://192.168.1.45:8765
```
Every time you press `Ctrl + S` in your editor on Laptop 1, the script instantly updates Laptop 2.

#### Option C: One-Off Send Command
```powershell
python autotyper.py send "C:\path\to\code.py" --server http://192.168.1.45:8765
```

---

### Step 3: Trigger & Control Typing on Laptop 2
The person on **Laptop 2** clicks into the target text box or IDE window and uses their hotkeys:

| Shortcut on Laptop 2 | Action |
| :--- | :--- |
| **`F8`** or **`Ctrl + Alt + Space`** | **Start typing** (5-second countdown gives time to focus window) |
| **`F8`** or **`Ctrl + Alt + Space`** (while typing) | **Pause** typing instantly |
| **`F8`** or **`Ctrl + Alt + Space`** (while paused) | **Resume** typing right where it stopped |
| **`Esc`** or **`Ctrl + Alt + C`** | **Emergency Stop / Cancel** & reset back to the start |
| **`Alt + =`** | **Slower** (increases delay by `+0.02s`) |
| **`Alt + -`** | **Faster** (decreases delay down to `0.001s` = 1,000 chars/s) |

---

## Part 2: Local Usage (Single Machine)

If you only want to use the AutoTyper locally on one machine:

1. **Install Prerequisites:**
   * Python 3.10+
   * `pip install pynput` (or run `pip install -r requirements.txt`)
2. **Text File:** Edit `~/autotype_text.txt` in your user home folder.
3. **Launch:** Run `python autotyper.py` or double-click `Start_AutoTyper.bat`.
4. **Trigger:** Press `F8` or `Ctrl + Alt + Space` to start, pause, or resume.

---

## Part 3: Built-in Keyboard Lock (`HP_Keyboard_Lock.ahk`)

Used when you place an external keyboard directly over a laptop's built-in keyboard to disable the built-in keys without affecting the external keyboard:

1. Install **AutoHotkey v2**.
2. Install the kernel driver from `Interception\command line installer`:
   ```cmd
   install-interception.exe /install
   ```
   *(Reboot Windows after installing)*.
3. Run `Monitor.ahk` to identify your laptop's keyboard hardware handle (e.g., `ACPI\VEN_ATK&DEV_3001`).
4. Set the handle in `HP_Keyboard_Lock.ahk` line 10.
5. Run `Start_Keyboard_Lock.bat`. Toggle on/off anytime with **Left Ctrl + Left Alt**.

---

## Code Structure

```text
autotyper/
├── config.py       # Configuration constants, delays, default ports
├── engine.py       # AutoTyper state machine, typing engine, text updater
├── hotkeys.py      # Global hotkey listener (F8, Ctrl+Alt+Space, Esc)
├── sync.py         # Cross-laptop HTTP sync server, REST API, Web UI, file watcher
├── win32_input.py  # Win32 SendInput, VirtualKey & hardware scan-code mappings
├── cli.py          # Command line runner (run, send, watch, stop)
├── selftest.py     # Built-in self-test suite (engine & sync server)
├── notify.py       # Notification hook
└── pid.py          # Single-instance process lock
```

### Useful Commands

* **Run Self-Test:**
  ```powershell
  python autotyper.py --self-test
  ```
* **Disable Server (Local only):**
  ```powershell
  python autotyper.py --no-server
  ```
* **Custom Sync Port:**
  ```powershell
  python autotyper.py --port 9000
  ```
* **Stop Background Instance:**
  ```powershell
  python autotyper.py stop
  ```
