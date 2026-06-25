# -*- coding: utf-8 -*-
# Cheapy Tool v1.0 — Configuration
# by psixakias.7 | discord.gg/cheapymarket

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

console = Console()

VERSION = "1.0"
AUTHOR = "psixakias.7"
DISCORD = "discord.gg/cheapymarket"
TOOLS_PER_PAGE = 10
GITHUB = "github.com/psixakias7/CheapyTool"
TOOL_NAME = "Cheapy Tool"
TOOL_VERSION = "1.0"

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

for d in [DATA_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


PORTS = load_json(DATA_DIR / "ports.json")
DEFAULT_PORTS = load_json(DATA_DIR / "default_ports.json")
VULN_PAYLOADS = load_json(DATA_DIR / "vuln_payloads.json")
VULN_ERRORS = load_json(DATA_DIR / "vuln_errors.json")
VULN_SENSITIVE_PATHS = load_json(DATA_DIR / "vuln_sensitive_paths.json")
USERNAME_PLATFORMS = load_json(DATA_DIR / "username_platforms.json")

USER_AGENTS_FILE = DATA_DIR / "user_agents.txt"

DEFAULT_TIMEOUT = 10
MAX_PORT = 65535

AFFIRMATIVE = {"y", "ye", "yes", "yeah", "ok", "okay", "1", "true"}
BLACKLIST_IPS = {"0.0.0.0"}

NEEDS_ADMIN: bool = False


def mark_admin_needed() -> None:
    global NEEDS_ADMIN
    NEEDS_ADMIN = True


THEME_COLORS = {
    "gold": {"primary": "#FFD700", "secondary": "#FFC107", "accent": "#FF8C00"},
}


class Theme:
    gold1 = "#FFB300"
    gold2 = "#FFD700"
    gold3 = "#FFC107"
    amber = "#FF8C00"
    dark_amber = "#CC7000"
    white = "#FFFFFF"
    light = "#FFF8E1"
    muted = "#665D3E"
    bg = "#0A0A0A"

    primary = gold1
    secondary = gold2
    accent = amber
    success = gold2
    error = amber
    info = gold3
    warning = gold2
    muted_text = muted

    GOLD_GRADIENT = [amber, gold1, gold2, gold3, gold2, gold1, amber]


BANNER = r"""
   ____ _   _ _____    _    ____  __   __
  / ___| | | | ____|  / \  |  _ \ \ \ / /
 | |   | |_| |  _|   / _ \ | |_) | \ V / 
 | |___|  _  | |___ / ___ \|  __/   | |  
  \____|_| |_|_____/_/   \_\_|      |_|  
"""

SUBBANNER = r"""
  +--------------------------------------------------+
  |       Cheapy Tool v1.0  |  54 Tools              |
  |  by psixakias.7  | discord.gg/cheapymarket        |
  |                                                    |
  |  BTC: bc1qygummake49msqz0c49tuzyp4ckz7zksycak6lp |
  |  LTC: LUjBajSshA2XUaX7M1kX49qWjjfjfh13V9         |
  +--------------------------------------------------+
"""


def print_banner():
    from colorama import Fore, Style
    print(Fore.YELLOW + Style.BRIGHT + BANNER + Style.RESET_ALL)
    print(Fore.YELLOW + SUBBANNER + Style.RESET_ALL)


def show_banner() -> None:
    print_banner()


def section_header(title: str) -> None:
    console.rule(Text(f" {title} ", style=f"bold {Theme.gold2}"), style=Theme.amber)


def info(msg: str) -> None:
    console.print(f"  [bold {Theme.gold3}][i][/] {msg}")


def success(msg: str) -> None:
    console.print(f"  [bold {Theme.gold2}][+][/] {msg}")


def error(msg: str) -> None:
    console.print(f"  [bold {Theme.amber}][x][/] {msg}")


def warning(msg: str) -> None:
    console.print(f"  [bold {Theme.gold2}][~][/] {msg}")


def wait_msg(msg: str) -> None:
    console.print(f"  [bold {Theme.gold3}][.][/] {msg}")


def get_input(prompt: str, default: str = "") -> str:
    val = console.input(f"  [bold {Theme.gold1}][>][/] {prompt} ")
    return val if val else default


def confirm(prompt: str = "Continue?") -> bool:
    return console.input(f"  [bold {Theme.gold1}][?][/] {prompt} (y/N) ").lower().strip() in AFFIRMATIVE


def pause() -> None:
    console.input(f"  [bold {Theme.muted_text}][Press Enter to continue...][/]")


def make_table(title: str = "", headers: list[str] | None = None) -> Table:
    t = Table(
        title=Text(title, style=Theme.gold1) if title else None,
        border_style=Theme.gold1,
        box=box.HEAVY_EDGE,
        header_style=f"bold {Theme.gold2}",
    )
    if headers:
        for h in headers:
            t.add_column(h)
    return t


def styled_error_box(msg: str) -> None:
    console.print(Panel(
        Text(f"  {msg}", style=f"bold {Theme.amber}"),
        border_style=Theme.amber,
        title=Text(" ERROR ", style=f"bold {Theme.amber}"),
        box=box.HEAVY,
    ))


def error_then_exit(msg: str) -> None:
    styled_error_box(msg)
    pause()
    sys.exit(1)


class Config:
    def __init__(self) -> None:
        self.http_timeout: float = DEFAULT_TIMEOUT
        self.socket_timeout: float = DEFAULT_TIMEOUT
        self.http_proxy: str | None = None
        self.socket_proxy: str | None = None
        self.user_agent: str = "CheapyTool/1.0"
        self.cookie: str | None = None
        self.json_output: bool = False

    def __repr__(self) -> str:
        return f"Config(http_timeout={self.http_timeout}, proxy={self.http_proxy})"
