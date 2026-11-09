#!/usr/bin/env python3
"""
Rock-Solid Auto-Typer using Python + pynput (Windows + Remote Keyboard Edition).

Compatibility entry point. The implementation is organized under the `autotyper/`
package:
  - autotyper/config.py    - constants and defaults
  - autotyper/win32_input.py - Win32 SendInput/VirtualKey helpers
  - autotyper/engine.py    - AutoTyper state machine and typing logic
  - autotyper/hotkeys.py   - global hotkey listener and modifier state
  - autotyper/pid.py       - single-instance PID helpers
  - autotyper/cli.py       - CLI and application runner
  - autotyper/selftest.py  - built-in self-test
  - autotyper/notify.py    - notification hook

Usage is unchanged:
  python autotyper.py
  python autotyper.py "C:\\path\\to\\custom_text.txt"
  python autotyper.py stop
  python autotyper.py --self-test
"""

from autotyper.cli import main


if __name__ == "__main__":
    main()
