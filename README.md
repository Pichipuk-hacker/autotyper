# Windows AutoTyper & Built-in Keyboard Lock (`AutoHotInterception`)

This repository contains two tools for Windows:
1. **AutoTyper** — A high-speed (1,000 chars/sec), remote-compatible Python Auto-Typer that reads text dynamically from `~/autotype_text.txt` on every start and sends real Win32 Virtual Keys (`wVk`) + Hardware Scan Codes (`wScan`). Works locally and across remote keyboard/desktop software (AnyDesk, Parsec, GlideX, RDP, Bluetooth HID, KVM). The implementation is organized as a package (`autotyper/`) with a compatibility entry point (`autotyper.py`).
2. **`HP_Keyboard_Lock.ahk`** — An AutoHotkey v2 + AutoHotInterception script that blocks selected keys (`A–Z`, `0–9`, `;`, `:`, `'`, `"`, `[`, `]`, `=`, `+`, `,`, `.`, `/`) **only on the laptop's built-in keyboard** while keeping your external USB/Bluetooth keyboard 100% functional.

A complete ready-to-use archive (**`AutoTyper_and_Keyboard_Lock_Bundle.zip`**) is also included directly in this repository.

---

## Quick Download (ZIP Bundle)

You can download **[`AutoTyper_and_Keyboard_Lock_Bundle.zip`](./AutoTyper_and_Keyboard_Lock_Bundle.zip)** directly from this repository. It includes:
- `autotyper.py`, the `autotyper/` package, & `Start_AutoTyper.bat`
- `HP_Keyboard_Lock.ahk` & `Start_Keyboard_Lock.bat`
- `autotype_text.txt` (sample text file)
- `AHI/` (pre-structured `C:\AHI` folder with `Monitor.ahk`, `AutoHotInterception.ahk`, `AutoHotInterception.dll`, `x86`/`x64` `interception.dll`, and `Unblocker.ps1`)
- `Interception/` (`install-interception.exe` command-line driver installer)

---

## Part 1: How to Run the AutoTyper (`autotyper.py`)

### 1. Prerequisites
1. Install **[Python 3.10+](https://www.python.org/downloads/)** (during installation, tick **"Add python.exe to PATH"**).
2. Install `pynput` in Command Prompt or PowerShell:
   ```powershell
   python -m pip install pynput
   ```

### 2. Prepare Your Text File (`autotype_text.txt`)
By default, `autotyper.py` reads from your Windows user home folder:
```text
C:\Users\<YourUsername>\autotype_text.txt
```
- Create or edit `C:\Users\<YourUsername>\autotype_text.txt` and paste the code/text you want typed.
- **No restart needed when editing:** The script re-reads `autotype_text.txt` automatically every time you trigger Start.

### 3. Start the AutoTyper
- **Option A (Batch Launcher):** Double-click **`Start_AutoTyper.bat`** (or run `python C:\AHI\autotyper.py`).
  *(Note: If your Python path differs, `Start_AutoTyper.bat` automatically falls back to `python` on your `PATH`.)*
- **Option B (Command Line):**
  ```powershell
  python autotyper.py
  ```
  You can also run the package directly:
  ```powershell
  python -m autotyper
  ```
  You can also pass a custom text file path:
  ```powershell
  python autotyper.py "C:\path\to\custom_text.txt"
  ```

### 4. AutoTyper Hotkeys

| Shortcut | Action |
| :--- | :--- |
| **`F8`** | **Start / Pause / Resume** typing *(Recommended when Keyboard Lock is active)* |
| **`Win + Alt`** | **Start / Pause / Resume** typing (either press order) |
| **`Ctrl + Alt + Space`** | **Start / Pause / Resume** typing |
| **`Ctrl + Alt + Enter`** | **Start / Pause / Resume** typing |
| **`Ctrl + Alt + X`** or **`Z`** | **Start / Pause / Resume** typing |
| **`Esc`** or **`Ctrl + Alt + C`** | **Emergency Stop / Cancel** and reset to beginning |
| **`Alt + =`** | **Slower** (increases per-character delay by `+0.02s`) |
| **`Alt + -`** | **Faster** (decreases per-character delay down to `0.001s` = 1,000 chars/s) |

### 5. Useful Commands
- Run built-in self-test:
  ```powershell
  python autotyper.py --self-test
  ```
- Stop a running background instance:
  ```powershell
  python autotyper.py stop
  ```

### 6. AutoTyper Code Structure
The AutoTyper code is split into focused modules under `autotyper/`:
- `config.py` — default paths, delays, and behavior constants
- `win32_input.py` — Win32 `SendInput`/virtual-key/scan-code helpers
- `engine.py` — `AutoTyper` state machine and typing logic
- `hotkeys.py` — global hotkey listener and modifier state
- `pid.py` — single-instance PID helpers
- `cli.py` — CLI and application runner
- `selftest.py` — built-in self-test
- `notify.py` — notification hook

`autotyper.py` remains a thin compatibility entry point, and `python -m autotyper` is also supported.

---

## Part 2: How to Set Up & Run the Built-in Keyboard Lock (`HP_Keyboard_Lock.ahk`)

### 1. Install Required Software
1. Install **[AutoHotkey v2](https://www.autohotkey.com/)**.
2. Extract the `AHI` folder from `AutoTyper_and_Keyboard_Lock_Bundle.zip` to **`C:\AHI`** so the layout is:
   ```text
   C:\AHI\
   ├── HP_Keyboard_Lock.ahk
   ├── Monitor.ahk
   ├── Start_Keyboard_Lock.bat
   ├── Start_AutoTyper.bat
   ├── autotyper.py
   ├── autotyper\
   │   ├── __init__.py
   │   ├── __main__.py
   │   ├── cli.py
   │   ├── config.py
   │   ├── engine.py
   │   ├── hotkeys.py
   │   ├── notify.py
   │   ├── pid.py
   │   ├── selftest.py
   │   └── win32_input.py
   └── Lib\
       ├── AutoHotInterception.ahk
       ├── AutoHotInterception.dll
       ├── CLR.ahk
       ├── Unblocker.ps1
       ├── x86\
       │   └── interception.dll
       └── x64\
           └── interception.dll
   ```
3. Unblock the files in PowerShell:
   ```powershell
   Get-ChildItem -Path "C:\AHI" -Recurse | Unblock-File
   ```

### 2. Install the Interception Driver (Administrator + Reboot)
1. Open **Command Prompt as Administrator**.
2. Navigate to the extracted `Interception\command line installer` folder and install:
   ```cmd
   cd /d "C:\Interception\command line installer"
   install-interception.exe /install
   ```
3. **Restart Windows** (required for the kernel driver to load).

### 3. Find Your Built-in Laptop Keyboard Handle
1. Run **`C:\AHI\Monitor.ahk`** with AutoHotkey v2.
2. Check each keyboard entry one at a time and press keys on your **built-in laptop keyboard**.
3. Copy the **Handle** of the keyboard that responds (for example, `ACPI\VEN_ATK&DEV_3001` or `ACPI\VEN_HPQ&DEV_8001`).
4. Close `Monitor.ahk`, open `C:\AHI\HP_Keyboard_Lock.ahk` in a text editor, and set line 10:
   ```autohotkey
   keyboardHandle := "ACPI\VEN_ATK&DEV_3001" ; <-- Replace with your laptop's handle
   ```

### 4. Run and Toggle the Keyboard Lock
1. Make sure your **external keyboard** is connected.
2. Double-click **`C:\AHI\Start_Keyboard_Lock.bat`** (or `HP_Keyboard_Lock.ahk`).
3. **Immediate Lock:** As soon as the script starts, the built-in laptop keyboard keys (`A–Z`, `0–9`, `;`, `:`, `'`, `"`, `[`, `]`, `=`, `+`, `,`, `.`, `/`) are **locked**.
4. **Toggle Lock On/Off:** Press **Left Ctrl + Left Alt** (in either order) at any time to unlock or re-lock the built-in keyboard.
5. **Exit & Restore:** Right-click the green **H** AutoHotkey icon in the system tray and click **Exit** to completely restore all keys.

