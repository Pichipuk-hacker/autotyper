"""Built-in self-test for the AutoTyper engine."""

import os
import tempfile
import time

from . import config, notify
from .engine import AutoTyper


def run_self_test():
    import autotyper.win32_input as win32_input

    orig_countdown = config.COUNTDOWN_SECONDS
    orig_notify = notify.notify
    orig_cleanup = win32_input.cleanup_modifiers
    orig_any_mod = win32_input.any_win32_modifier_down
    orig_caps = win32_input.ensure_capslock_off

    config.COUNTDOWN_SECONDS = 0.2
    notify.notify = lambda msg: None
    win32_input.cleanup_modifiers = lambda d=None: None
    win32_input.any_win32_modifier_down = lambda: False
    win32_input.ensure_capslock_off = lambda: None
    # engine imported these names directly
    import autotyper.engine as engine

    orig_e_cleanup = engine.cleanup_modifiers
    orig_e_any = engine.any_win32_modifier_down
    orig_e_caps = engine.ensure_capslock_off
    engine.cleanup_modifiers = win32_input.cleanup_modifiers
    engine.any_win32_modifier_down = win32_input.any_win32_modifier_down
    engine.ensure_capslock_off = win32_input.ensure_capslock_off

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("ab\nc")
        path = f.name

    try:
        typed = []
        t = AutoTyper(file_path=path)
        for sample_ch in ("a", "A", "1", "(", ")", "=", "+", "\n", "\t"):
            assert t._resolve(sample_ch) is not None, sample_ch
        t._type_char = lambda ch: (t._resolve(ch) is not None) and (typed.append(ch) or True)
        t._newline = lambda: typed.append("\n")

        t.toggle()
        t.worker_thread.join(timeout=5)
        assert typed == ["a", "b", "\n", "c"], typed
        assert t.state == "STOPPED", t.state

        typed.clear()
        t.toggle()
        time.sleep(0.05)
        t.cancel()
        t.worker_thread.join(timeout=5)
        assert typed == [], typed
        assert t.state == "STOPPED", t.state

        t.adjust_delay(+10.0)
        assert t.delay == 1.0, t.delay
        t.adjust_delay(-10.0)
        assert t.delay == 0.001, t.delay

        print("self-test: OK")
    finally:
        os.remove(path)
        config.COUNTDOWN_SECONDS = orig_countdown
        notify.notify = orig_notify
        win32_input.cleanup_modifiers = orig_cleanup
        win32_input.any_win32_modifier_down = orig_any_mod
        win32_input.ensure_capslock_off = orig_caps
        engine.cleanup_modifiers = orig_e_cleanup
        engine.any_win32_modifier_down = orig_e_any
        engine.ensure_capslock_off = orig_e_caps
