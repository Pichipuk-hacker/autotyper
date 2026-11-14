"""CLI entry point and application runner."""

import argparse
import os
import signal
import sys
import threading

from . import config, pid
from .engine import AutoTyper
from .selftest import run_self_test
from .sync import normalize_server_url, send_file, send_text, start_sync_server, watch_file


def run_app(file_path, enable_server=True, host=config.SYNC_HOST, port=config.SYNC_PORT):
    typer = AutoTyper(file_path=file_path)

    server = None
    server_info = ""
    if enable_server:
        try:
            server, lan_ip, bound_port = start_sync_server(typer, host=host, port=port)
            server_info = f"""Sync Server    : Active on port {bound_port}
Web Dashboard  : http://{lan_ip}:{bound_port} (Open this on Laptop 1 or phone!)
Local URL      : http://localhost:{bound_port}"""
        except Exception as e:
            server_info = f"Sync Server    : Failed to start ({e})"

    print("=" * 60)
    print("AutoTyper Active & Listening (Windows + Remote Keyboard)")
    print("=" * 60)
    print(f"Reading from   : {file_path}")
    if server_info:
        print(server_info)
    print("-" * 60)
    print("Hotkeys (Physical Keyboard on this Laptop):")
    print("  - Ctrl + Alt + Space : Toggle (Start / Pause / Resume) [Recommended]")
    print("  - Ctrl + Alt + Enter : Toggle Alternative")
    print("  - Ctrl + Alt + X / Z : Toggle Alternative")
    print("  - Win + Alt          : Toggle Alternative")
    print("  - F8                 : Toggle Alternative")
    print("  - Escape / Ctrl+Alt+C: Emergency Stop / Cancel (when active)")
    print("  - Alt + =            : Slower (increase delay)")
    print("  - Alt + -            : Faster (decrease delay)")
    print("=" * 60)
    print("Tip: Type on Laptop 1 in the Web Dashboard or edit the file anytime!")
    print("Press Ctrl+C in this terminal to exit.\n")

    # Start keyboard listener
    from . import hotkeys
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
        if server:
            try:
                server.shutdown()
            except Exception:
                pass
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="AutoTyper with Cross-Laptop Sync Support",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to run")

    # 'send' subcommand (for Laptop 1)
    send_parser = subparsers.add_parser("send", help="Send a file or text to Laptop 2")
    send_parser.add_argument("target", help="File path or text string to send")
    send_parser.add_argument("--server", default=f"http://localhost:{config.SYNC_PORT}", help="Laptop 2 server URL")

    # 'watch' subcommand (for Laptop 1)
    watch_parser = subparsers.add_parser("watch", help="Watch a local file and sync on every save")
    watch_parser.add_argument("file", help="Local file path to watch")
    watch_parser.add_argument("--server", default=f"http://localhost:{config.SYNC_PORT}", help="Laptop 2 server URL")
    watch_parser.add_argument("--interval", type=float, default=0.5, help="Polling interval in seconds")

    # General options for runner
    parser.add_argument("file_or_command", nargs="?", default=None, help="File path, or 'stop'/'cancel'")
    parser.add_argument("--no-server", action="store_true", help="Disable the background sync server")
    parser.add_argument("--port", type=int, default=config.SYNC_PORT, help="Port for the sync server")
    parser.add_argument("--host", default=config.SYNC_HOST, help="Bind host for the sync server")
    parser.add_argument("--self-test", action="store_true", help="Run the built-in self-test suite")

    return parser.parse_args(argv)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    # Handle quick subcommands or positional flags
    if len(argv) > 0 and argv[0].lower() in ("stop", "kill", "cancel"):
        pid.stop_existing()
        return

    if "--self-test" in argv:
        run_self_test()
        return

    # Check for send/watch subcommands
    if len(argv) > 0 and argv[0] in ("send", "watch"):
        args = parse_args(argv)
        if args.subcommand == "send":
            target = args.target
            url = args.server
            if os.path.isfile(target):
                res = send_file(url, target)
            else:
                res = send_text(url, target)
            chars = res.get("chars", 0)
            lines = res.get("lines", 0)
            print(f"[AutoTyper Sync] Successfully sent {chars} chars ({lines} lines) to {url}")
            return
        elif args.subcommand == "watch":
            watch_file(args.server, args.file, interval=args.interval)
            return

    # Normal runner (Laptop 2 / Local)
    target_file = config.DEFAULT_FILE
    enable_server = config.SYNC_ENABLED
    port = config.SYNC_PORT
    host = config.SYNC_HOST

    args = parse_args(argv)
    if args.file_or_command:
        if args.file_or_command.lower() in ("stop", "kill", "cancel"):
            pid.stop_existing()
            return
        elif os.path.isfile(args.file_or_command):
            target_file = os.path.abspath(args.file_or_command)
        else:
            target_file = os.path.abspath(args.file_or_command)

    if args.no_server:
        enable_server = False
    if args.port:
        port = args.port
    if args.host:
        host = args.host

    existing = pid.read_pid()
    if existing and existing != os.getpid() and pid.pid_alive(existing) and pid.is_autotyper(existing):
        print(f"AutoTyper is already running (PID {existing}). Use 'stop' first.")
        return

    with open(config.PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        run_app(target_file, enable_server=enable_server, host=host, port=port)
    finally:
        pid.remove_pid_file()
