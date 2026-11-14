"""AutoTyper state machine and typing engine."""

import ctypes
import os
import random
import threading
import time

from . import config, hotkeys, notify
from .win32_input import (
    VK_BACK,
    VK_END,
    VK_HOME,
    VK_LCONTROL,
    VK_LMENU,
    VK_LSHIFT,
    VK_RETURN,
    VK_TAB,
    any_win32_modifier_down,
    cleanup_modifiers,
    ensure_capslock_off,
    make_unicode_input,
    make_vk_input,
    send_inputs,
    user32,
)


class AutoTyper:
    def __init__(self, file_path=None, delay=None):
        self.file_path = file_path if file_path is not None else config.DEFAULT_FILE
        self.delay = delay if delay is not None else config.CHAR_DELAY
        self.text = ""
        self.state = "STOPPED"  # STOPPED / COUNTDOWN / RUNNING / PAUSED / RESUMING
        self.index = 0
        self.gen = 0
        self._paused_from = None
        self._typing = False
        self.cond = threading.Condition()
        self.worker_thread = None
        self._xlock = threading.Lock()
        self._display = None
        self._charcache = {}

    def _rebuild_keymap(self):
        self._charcache.clear()

    # ---- text loading -------------------------------------------------
    def load_text(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().replace("\r\n", "\n").replace("\r", "\n")
                if content.strip():
                    return content
                print(f"[AutoTyper] Warning: {self.file_path} is empty; using fallback text.")
            except Exception as e:
                print(f"[AutoTyper] Warning: Could not read {self.file_path}: {e}")
        else:
            if self.text and self.text.strip():
                return self.text
            print(f"[AutoTyper] Warning: {self.file_path} not found; using fallback text.")
        if self.text and self.text.strip():
            return self.text
        return config.FALLBACK_TEXT

    # ---- low-level Win32 VirtualKey + ScanCode SendInput --------------
    def _resolve(self, ch):
        if ch in self._charcache:
            return self._charcache[ch]
        if ch in ("\n", "\r"):
            res = (VK_RETURN, 0)
        elif ch == "\t":
            res = (VK_TAB, 0)
        else:
            try:
                raw = user32.VkKeyScanW(ch)
            except ctypes.ArgumentError:
                raw = user32.VkKeyScanW(ord(ch))
            vk_scan = ctypes.c_short(raw).value
            if vk_scan == -1:
                res = None
            else:
                vk = vk_scan & 0xFF
                shift_state = (vk_scan >> 8) & 0xFF
                res = (vk, shift_state)
        self._charcache[ch] = res
        return res

    def _tap_vk(self, vk):
        send_inputs([make_vk_input(vk, False), make_vk_input(vk, True)])

    def _type_char(self, ch):
        resolved = self._resolve(ch)
        try:
            with self._xlock:
                if resolved is not None:
                    vk, shift_state = resolved
                    need_shift = bool(shift_state & 1)
                    need_ctrl = bool(shift_state & 2)
                    need_alt = bool(shift_state & 4)
                    events = []
                    if need_ctrl:
                        events.append(make_vk_input(VK_LCONTROL, False))
                    if need_alt:
                        events.append(make_vk_input(VK_LMENU, False))
                    if need_shift:
                        events.append(make_vk_input(VK_LSHIFT, False))
                    events.append(make_vk_input(vk, False))
                    events.append(make_vk_input(vk, True))
                    if need_shift:
                        events.append(make_vk_input(VK_LSHIFT, True))
                    if need_alt:
                        events.append(make_vk_input(VK_LMENU, True))
                    if need_ctrl:
                        events.append(make_vk_input(VK_LCONTROL, True))
                    return send_inputs(events)

                # Fallback for non-keyboard Unicode symbols (emojis, etc.)
                utf16_bytes = ch.encode("utf-16-le")
                code_units = [
                    int.from_bytes(utf16_bytes[i : i + 2], "little")
                    for i in range(0, len(utf16_bytes), 2)
                ]
                events = []
                for cu in code_units:
                    events.append(make_unicode_input(cu, key_up=False))
                    events.append(make_unicode_input(cu, key_up=True))
                return send_inputs(events)
        except Exception as e:
            print(f"[AutoTyper] Error typing {ch!r}: {e}")
            return False

    def _newline(self):
        with self._xlock:
            self._tap_vk(VK_RETURN)
            # Give target editor breathing room to process newline
            time.sleep(0.040)

            if config.SMART_INDENT:
                # Safely delete auto-inserted indentation on the current line:
                # Shift+Home selects back to column 0 on the CURRENT line, then Backspace deletes it.
                # Never selects forward or touches previous lines.
                events = [
                    make_vk_input(VK_LSHIFT, False),
                    make_vk_input(VK_HOME, False),
                    make_vk_input(VK_HOME, True),
                    make_vk_input(VK_LSHIFT, True),
                    make_vk_input(VK_BACK, False),
                    make_vk_input(VK_BACK, True),
                ]
                send_inputs(events)
                time.sleep(0.015)

    def _wait_for_modifiers_release(self):
        # Wait up to 1.5s for user to physically release start/resume hotkeys.
        t_end = time.monotonic() + 1.5
        while time.monotonic() < t_end:
            if not (hotkeys.has_ctrl() or hotkeys.has_alt() or hotkeys.has_cmd() or any_win32_modifier_down()):
                break
            time.sleep(0.03)
        with self._xlock:
            cleanup_modifiers()
            ensure_capslock_off()
        hotkeys.clear_pressed()
        time.sleep(0.05)

    def _worker(self, gen):
        # Countdown. Pauses freeze the remaining time; cancel bumps `gen`.
        remaining = float(config.COUNTDOWN_SECONDS)
        with self.cond:
            while remaining > 0:
                while self.state == "PAUSED":
                    self.cond.wait()
                if self.gen != gen or self.state != "COUNTDOWN":
                    return
                t0 = time.monotonic()
                self.cond.wait(timeout=min(0.1, remaining))
                remaining -= time.monotonic() - t0

            while self.state == "PAUSED":
                self.cond.wait()
            if self.gen != gen or self.state != "COUNTDOWN":
                return
            self._wait_for_modifiers_release()
            self.state = "RUNNING"
            total = len(self.text)

        print(f"[AutoTyper] Typing started ({total} characters)...")
        notify.notify("Typing started")

        resumed_from_pause = False
        next_deadline = time.perf_counter()
        while True:
            with self.cond:
                while self.state == "PAUSED":
                    self.cond.wait()
                if self.gen != gen or self.state not in ("RUNNING", "RESUMING"):
                    return

                if self.state == "RESUMING":
                    # Grace period on resume so fingers leave Ctrl+Alt before typing
                    rem = 0.8
                    while rem > 0 and self.state == "RESUMING":
                        t0 = time.monotonic()
                        self.cond.wait(timeout=min(0.1, rem))
                        rem -= time.monotonic() - t0
                    if self.gen != gen or self.state != "RESUMING":
                        continue
                    self.state = "RUNNING"
                    resumed_from_pause = True

                if self.index >= len(self.text):
                    self.state = "STOPPED"
                    self.cond.notify_all()
                    done, ch, line_start = True, None, False
                else:
                    done, ch = False, self.text[self.index]
                    line_start = self.index == 0 or self.text[self.index - 1] == "\n"

            if done:
                print("[AutoTyper] Finished typing!")
                notify.notify("Finished typing!")
                return

            if resumed_from_pause:
                self._wait_for_modifiers_release()
                resumed_from_pause = False
                next_deadline = time.perf_counter()

            self._typing = True
            try:
                if ch == "\n":
                    self._newline()
                    ok = True
                elif ch == "\t" and line_start:
                    # Typing Tab with a selection can indent the whole line in
                    # some IDEs; emit spaces instead.
                    ok = True
                    for _ in range(config.TAB_WIDTH):
                        ok = self._type_char(" ") and ok
                else:
                    ok = self._type_char(ch)
            finally:
                self._typing = False
            if not ok:
                print(f"[AutoTyper] Could not type {ch!r}; skipping.")

            with self.cond:
                # Only advance for the worker that still owns this session.
                if self.gen == gen and self.state in ("RUNNING", "PAUSED", "RESUMING"):
                    self.index += 1

            nap = self.delay
            if config.HUMAN_JITTER:
                nap *= random.uniform(0.6, 1.4)
            next_deadline += nap
            rem_wait = next_deadline - time.perf_counter()
            if rem_wait > 0.004:
                with self.cond:
                    if self.gen == gen and self.state == "RUNNING":
                        self.cond.wait(timeout=rem_wait - 0.002)
            while time.perf_counter() < next_deadline:
                if self.gen != gen or self.state != "RUNNING":
                    break

    # ---- controls -----------------------------------------------------
    def toggle(self):
        if self.state == "STOPPED":
            text = self.load_text()  # file IO outside the lock
            self._rebuild_keymap()
            with self.cond:
                if self.state != "STOPPED":
                    return
                self.text = text
                self.index = 0
                self.gen += 1
                self._paused_from = None
                self.state = "COUNTDOWN"
                self.worker_thread = threading.Thread(
                    target=self._worker, args=(self.gen,), daemon=True
                )
                self.worker_thread.start()
                self.cond.notify_all()
                chars, lines = len(self.text), len(self.text.splitlines())
            print(f"[AutoTyper] Loaded {chars} chars ({lines} lines) from {self.file_path}")
            print(f"[AutoTyper] Starting in {config.COUNTDOWN_SECONDS}s...")
            notify.notify(f"Starting in {config.COUNTDOWN_SECONDS}s...")
            return

        with self.cond:
            if self.state in ("COUNTDOWN", "RUNNING", "RESUMING"):
                self._paused_from = self.state
                self.state = "PAUSED"
                self.cond.notify_all()
                action = "paused"
            elif self.state == "PAUSED":
                self.state = "RESUMING"
                self.cond.notify_all()
                action = "resumed"
            else:
                return

        if action == "paused":
            with self._xlock:
                cleanup_modifiers()
            hotkeys.clear_pressed()
            print("[AutoTyper] Paused.")
            notify.notify("Paused (Ctrl+Alt+Space to resume, Esc to stop)")
        else:
            print("[AutoTyper] Resuming in 0.8s...")
            notify.notify("Resuming in 0.8s...")

    def cancel(self):
        was_active = False
        with self.cond:
            if self.state != "STOPPED":
                was_active = True
                self.gen += 1  # invalidate any running worker
                self.state = "STOPPED"
                self.index = 0
                self.cond.notify_all()
        with self._xlock:
            cleanup_modifiers()
        hotkeys.clear_pressed()
        if was_active:
            notify.notify("Stopped & Cancelled")
            print("[AutoTyper] Cancelled & Reset.")

    def adjust_delay(self, delta):
        with self.cond:
            self.delay = round(max(0.001, min(1.0, self.delay + delta)), 3)
            delay = self.delay
        cps = 1.0 / delay if delay > 0 else 0
        direction = "Slower" if delta > 0 else "Faster"
        msg = f"Delay: {delay:.3f}s (~{cps:.1f} chars/s) [{direction}]"
        print(f"[AutoTyper] {msg}")
        notify.notify(msg)

    def set_delay(self, val):
        with self.cond:
            self.delay = round(max(0.001, min(1.0, float(val))), 4)
            delay = self.delay
        cps = 1.0 / delay if delay > 0 else 0
        msg = f"Delay set to {delay:.3f}s (~{cps:.1f} chars/s)"
        print(f"[AutoTyper] {msg}")
        notify.notify(msg)

    def update_text(self, new_text, save_file=True):
        cleaned = (new_text or "").replace("\r\n", "\n").replace("\r", "\n")
        with self.cond:
            self.text = cleaned
            if self.state == "STOPPED":
                self.index = 0
            self._rebuild_keymap()
            total = len(self.text)
            lines = len(self.text.splitlines()) if self.text else 0
        if save_file and self.file_path:
            try:
                parent = os.path.dirname(os.path.abspath(self.file_path))
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write(self.text)
            except Exception as e:
                print(f"[AutoTyper] Warning: Could not write updated text to {self.file_path}: {e}")
        print(f"[AutoTyper Sync] Text updated ({total} chars, {lines} lines)")
        return total

    def get_status(self):
        with self.cond:
            delay = self.delay
            cps = round(1.0 / delay, 1) if delay > 0 else 1000.0
            total = len(self.text) if self.text else 0
            prog = round((self.index / total * 100), 1) if total > 0 else 0.0
            return {
                "state": self.state,
                "index": self.index,
                "total": total,
                "delay": round(delay, 4),
                "chars_per_sec": cps,
                "file_path": self.file_path,
                "progress_percent": prog,
                "smart_indent": config.SMART_INDENT,
            }
