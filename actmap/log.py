#!/usr/bin/env python3
"""
Enhanced logging module - colored output, controlled by debug mode
"""

import sys
from typing import Any

# Color codes
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m', 
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'gray': '\033[90m',
    'reset': '\033[0m'
}

# Global debug flag
_debug_mode = False


def set_debug(debug: bool):
    """Set debug mode"""
    global _debug_mode
    _debug_mode = debug


def is_debug() -> bool:
    """Return whether currently in debug mode"""
    return _debug_mode


def colored(text: str, color: str) -> str:
    """Add color to text"""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def debug(*args: Any, **kwargs: Any):
    """Debug information - only shown in debug mode (cyan)"""
    if _debug_mode:
        message = " ".join(str(arg) for arg in args)
        print(colored("🐛 DEBUG:", "cyan"), colored(message, "cyan"), **kwargs)


def info(*args: Any, **kwargs: Any):
    """General information - always shown (blue)"""
    message = " ".join(str(arg) for arg in args)
    print(colored("ℹ️ INFO:", "blue"), colored(message, "blue"), **kwargs)


def success(*args: Any, **kwargs: Any):
    """Success information - always shown (green)"""
    message = " ".join(str(arg) for arg in args)
    print(colored("✅ SUCCESS:", "green"), colored(message, "green"), **kwargs)


def warning(*args: Any, **kwargs: Any):
    """Warning information - always shown (yellow)"""
    message = " ".join(str(arg) for arg in args)
    print(colored("⚠️ WARNING:", "yellow"), colored(message, "yellow"), **kwargs, file=sys.stderr)


def error(*args: Any, **kwargs: Any):
    """Error information - always shown (red)"""
    message = " ".join(str(arg) for arg in args)
    print(colored("❌ ERROR:", "red"), colored(message, "red"), **kwargs, file=sys.stderr)


def fatal(*args: Any, **kwargs: Any):
    """Fatal error information - always shown and exit"""
    error(*args, **kwargs)
    sys.exit(1)


def debug_plain(*args: Any, **kwargs: Any):
    """Debug information (no icon) - only shown in debug mode (gray)"""
    if _debug_mode:
        message = " ".join(str(arg) for arg in args)
        print(colored(message, "gray"), **kwargs)


def info_plain(*args: Any, **kwargs: Any):
    """General information (no icon) - always shown"""
    print(*args, **kwargs)


# Concise versions (for progress updates, etc.)
def progress(*args: Any, **kwargs: Any):
    """Progress information - always shown (magenta)"""
    message = " ".join(str(arg) for arg in args)
    print(colored("⏳", "magenta"), colored(message, "magenta"), **kwargs)


def step(*args: Any, **kwargs: Any):
    """Step information - always shown (blue)"""
    message = " ".join(str(arg) for arg in args)
    print(colored("➡️", "blue"), colored(message, "blue"), **kwargs)