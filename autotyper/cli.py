"""CLI entry point and application runner."""

import os
import signal
import sys
import threading

from . import hotkeys, pid
from .config import DEFAULT_FILE, PID_FILE
from .engine import AutoTyper
from .selftest import run_self_test


def run_app(file_path):
    typer = AutoTyper(file_path=file_path)

    print("=" * 60)
    print("AutoTyper Active & Listening (Windows + Remote Keyboard)")
    print("=" * 60)
    print(f"Reading from : {file_path}")
    print("Hotkeys:")
    print("  - Ctrl + Alt + Space : Toggle (Start / Pause / Resume) [Recommended]")
    print("  - Ctrl + Alt + Enter : Toggle Alternative")
    print("  - Ctrl + Alt + X / Z : Toggle Alternative")
    print("  - Win + Alt          : Toggle Alternative")
    print("  - F8                 : Toggle Alternative")
    print("  - Escape / Ctrl+Alt+C: Emergency Stop / Cancel (when active)")
    print("  - Alt + =            : Slower (increase delay)")
    print("  - Alt + -            : Faster (decrease delay)")
    print("=" * 60)
    print("Tip: Edit the text file anytime; it re-reads on every Start!")
    print("Press Ctrl+C in this terminal to exit.\n")

    listener = hotkeys.start_listener(typer)
    stop_event = threading.Event()

    def _handle_signal(signum, frame):
        stop_event.set()

    previous_term = signal.signal(signal.SIGTERM, _handle_signal)
    previous_int = signal.signal(signal.SIGINT, _handle_signal)

    try:
        while not stop_event.wait(0.5):
            pass
    finally:
        typer.cancel()
        listener.stop()
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    target_file = DEFAULT_FILE

    if len(argv) > 0:
        arg = argv[0]
        if arg.lower() in ("stop", "kill", "cancel"):
            pid.stop_existing()
            return
        elif arg == "--self-test":
            run_self_test()
            return
        elif os.path.isfile(arg):
            target_file = os.path.abspath(arg)

    existing = pid.read_pid()
    if existing and existing != os.getpid() and pid.pid_alive(existing) and pid.is_autotyper(existing):
        print(f"AutoTyper is already running (PID {existing}). Use 'stop' first.")
        return

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        run_app(target_file)
    finally:
        pid.remove_pid_file()
