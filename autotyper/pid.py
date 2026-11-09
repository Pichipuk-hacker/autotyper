"""PID file helpers for single-instance management (Windows-compatible)."""

import ctypes
import os
import signal
import subprocess
from ctypes import wintypes

from .config import PID_FILE
from .win32_input import kernel32


def read_pid():
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def pid_alive(pid):
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not handle:
        return False
    try:
        exit_code = wintypes.DWORD()
        if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return exit_code.value == STILL_ACTIVE
        return True
    finally:
        kernel32.CloseHandle(handle)


def is_autotyper(pid):
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}').CommandLine"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return "autotyper" in (res.stdout or "").lower()
    except Exception:
        return True


def remove_pid_file():
    try:
        if read_pid() == os.getpid():
            os.remove(PID_FILE)
    except Exception:
        pass


def stop_existing():
    pid = read_pid()
    if pid is None:
        print("AutoTyper is not running.")
        return
    if not pid_alive(pid):
        print(f"AutoTyper is not running (stale PID {pid}).")
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
        return
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent stop signal to AutoTyper (PID {pid}).")
    except Exception as e:
        print(f"Could not kill process: {e}")
