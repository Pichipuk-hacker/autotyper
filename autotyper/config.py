"""Configuration constants for AutoTyper."""

import os

# Default file location to read text from:
DEFAULT_FILE = os.path.expanduser("~/autotype_text.txt")

# Fallback text if the file doesn't exist:
FALLBACK_TEXT = """def hello():
    print("Hello, World!")

hello()"""

# Delay between characters in seconds.
# 0.015s = ~65 chars/s (Fast, rock-solid, and never drops lines or buffer overflows)
# Can be adjusted on-the-fly via Web Dashboard, Alt + = / Alt + -, or CLI.
CHAR_DELAY = 0.015

# Countdown in seconds before typing starts
COUNTDOWN_SECONDS = 5

PID_FILE = os.path.expanduser("~/.autotyper.pid")

# Spaces per indent level (used when the file uses tabs)
TAB_WIDTH = 4

# SMART_INDENT: True by default. Safely clears the editor's auto-inserted indentation
# so that indentation exactly matches the source file without double-indentation.
SMART_INDENT = True

# Slightly vary the delay between keys so typing looks natural and never floods event queues.
HUMAN_JITTER = True

# Cross-Laptop Sync Server defaults
SYNC_ENABLED = True
SYNC_PORT = 8765
SYNC_HOST = "0.0.0.0"
