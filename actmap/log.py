#!/usr/bin/env python3
"""
增强版日志模块 - 带颜色输出，根据调试模式控制显示
"""

import sys
from typing import Any

# 颜色代码
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

# 全局调试标志
_debug_mode = False


def set_debug(debug: bool):
    """设置调试模式"""
    global _debug_mode
    _debug_mode = debug


def is_debug() -> bool:
    """返回当前是否是调试模式"""
    return _debug_mode


def colored(text: str, color: str) -> str:
    """给文本添加颜色"""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def debug(*args: Any, **kwargs: Any):
    """调试信息 - 只在调试模式下显示（青色）"""
    if _debug_mode:
        message = " ".join(str(arg) for arg in args)
        print(colored("🐛 DEBUG:", "cyan"), colored(message, "cyan"), **kwargs)


def info(*args: Any, **kwargs: Any):
    """普通信息 - 始终显示（蓝色）"""
    message = " ".join(str(arg) for arg in args)
    print(colored("ℹ️ INFO:", "blue"), colored(message, "blue"), **kwargs)


def success(*args: Any, **kwargs: Any):
    """成功信息 - 始终显示（绿色）"""
    message = " ".join(str(arg) for arg in args)
    print(colored("✅ SUCCESS:", "green"), colored(message, "green"), **kwargs)


def warning(*args: Any, **kwargs: Any):
    """警告信息 - 始终显示（黄色）"""
    message = " ".join(str(arg) for arg in args)
    print(colored("⚠️ WARNING:", "yellow"), colored(message, "yellow"), **kwargs, file=sys.stderr)


def error(*args: Any, **kwargs: Any):
    """错误信息 - 始终显示（红色）"""
    message = " ".join(str(arg) for arg in args)
    print(colored("❌ ERROR:", "red"), colored(message, "red"), **kwargs, file=sys.stderr)


def fatal(*args: Any, **kwargs: Any):
    """致命错误信息 - 始终显示并退出"""
    error(*args, **kwargs)
    sys.exit(1)


def debug_plain(*args: Any, **kwargs: Any):
    """调试信息（无图标） - 只在调试模式下显示（灰色）"""
    if _debug_mode:
        message = " ".join(str(arg) for arg in args)
        print(colored(message, "gray"), **kwargs)


def info_plain(*args: Any, **kwargs: Any):
    """普通信息（无图标） - 始终显示"""
    print(*args, **kwargs)


# 简洁版本（用于进度更新等）
def progress(*args: Any, **kwargs: Any):
    """进度信息 - 始终显示（品红色）"""
    message = " ".join(str(arg) for arg in args)
    print(colored("⏳", "magenta"), colored(message, "magenta"), **kwargs)


def step(*args: Any, **kwargs: Any):
    """步骤信息 - 始终显示（蓝色）"""
    message = " ".join(str(arg) for arg in args)
    print(colored("➡️", "blue"), colored(message, "blue"), **kwargs)