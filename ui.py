# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import os
import random
import shutil
import sys
import time as _time
from datetime import datetime
from typing import Any

from colorama import Fore, Style

from rich.control import Control
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich import box

from config import Theme, TOOL_NAME, TOOL_VERSION, OUTPUT_DIR, console, NEEDS_ADMIN

GOLD_COLORS = ["#FF8C00", "#FFB300", "#FFD700", "#FFC107", "#FFD700", "#FFB300", "#FF8C00"]
COLOR_THEMES = {
    "gold":   {"p": "#FFB300", "s": "#FFD700", "a": "#FF8C00", "m": "#665D3E", "bg": "#0A0A0A"},
    "silver": {"p": "#C0C0C0", "s": "#E8E8E8", "a": "#A0A0A0", "m": "#666666", "bg": "#0A0A0A"},
    "bronze": {"p": "#CD7F32", "s": "#DAA520", "a": "#8B4513", "m": "#665544", "bg": "#0A0A0A"},
    "neon":   {"p": "#00FF88", "s": "#00FFFF", "a": "#FF00FF", "m": "#444444", "bg": "#050510"},
}

WINBEEP = None
try:
    import winsound
    WINBEEP = winsound.Beep
except ImportError:
    pass


def beep(freq=800, dur=100):
    if WINBEEP:
        WINBEEP(freq, dur)


TOOLS_PER_PAGE = 10


CATEGORY_ICONS = {
    "Network": "[NET] Network",
    "OSINT": "[OSI] OSINT",
    "Discord": "[DSC] Discord",
    "Utils": "[UTL] Utils",
    "System": "[SYS] System",
    "Webhook": "[WHK] Webhook",
    "Admin": "[ADM] Admin",
    "Social": "[SOC] Social",
    "Gen": "[GEN] Gen",
    "Web": "[WEB] Web",
}

CATEGORY_COLORS = {
    "Network": "#00BFFF",
    "OSINT": "#FFD700",
    "Discord": "#7289DA",
    "Utils": "#FFC107",
    "System": "#FF8C00",
    "Webhook": "#FF6B6B",
    "Admin": "#FF4444",
    "Social": "#FF69B4",
    "Gen": "#00FF7F",
    "Web": "#00FF7F",
}


def get_default_color(cat: str) -> str:
    return CATEGORY_COLORS.get(cat, Theme.gold2)


def get_category_icon(cat: str) -> str:
    return CATEGORY_ICONS.get(cat, cat)


def typewriter(text: str, delay: float = 0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        _time.sleep(delay)
    print()


def startup_animation():
    os.system('cls')
    typewriter("  > Initializing Cheapy Tool v1.0...", 0.03)
    typewriter("  > Loading 54 modules...", 0.02)
    typewriter("  > Bypassing security protocols...", 0.02)
    typewriter("  > Establishing secure connection...", 0.02)
    typewriter("  > discord.gg/cheapymarket", 0.04)
    _time.sleep(0.5)
    os.system('cls')


def matrix_rain():
    chars = "\uff71\uff72\uff73\uff74\uff75\uff76\uff77\uff78\uff79\uff7a\uff7b\uff7c\uff7d\uff7e\uff7f\uff80\uff81\uff82\uff83\uff84\uff85\uff86\uff87\uff88\uff89\uff8a\uff8b\uff8c\uff8d\uff8e\uff8f\uff90\uff91\uff92\uff93\uff940123456789CHEAPYTOOL"
    cols = shutil.get_terminal_size().columns
    for _ in range(8):
        line = ""
        for _ in range(cols):
            if random.random() > 0.7:
                line += f"\033[93m{random.choice(chars)}\033[0m"
            else:
                line += " "
        print(line)
        _time.sleep(0.08)
    _time.sleep(0.3)
    os.system('cls')


# ─── COMPACT HEADER (replaces old 8-row ASCII logo) ──


def make_header_panel() -> Panel:
    t = Text()
    t.append("  [!]  discord.gg/cheapymarket", style="bold #FFD700")
    t.append(" " * 20, style="")
    t.append("made by psixakias.7  [!]", style="bold #FFC107")
    return Panel(t, border_style=Theme.gold1, box=box.SIMPLE)


# ─── SKULL BANNER ──────────────────────────────


def get_skull_banner() -> Panel:
    t = Text(justify="center")
    t.append("  [*]  CHEAPY TOOL -- THE ULTIMATE HACKER ARSENAL  [*]  ", style="bold #FFD700")
    return Panel(t, border_style="#8B6914", box=box.SIMPLE)


# ─── NAV BAR ────────────────────────────────────


def get_nav_bar(page: int, total: int) -> Panel:
    t = Text(justify="center")
    t.append("  << [A] PREV    |    ", style=Theme.muted_text)
    t.append(f"Page {page} of {total}", style=f"bold {Theme.gold1}")
    t.append("    |    [D] NEXT >>  ", style=Theme.muted_text)
    return Panel(t, border_style=Theme.amber, box=box.SIMPLE)


# ─── TOOLS TABLE ───────────────────────────────


def get_tools_table(items, current_page: int = 0, page_size: int = 15, favorites: set | None = None) -> Panel:
    favorites = favorites or set()
    start = current_page * page_size
    end = start + page_size
    page_items = items[start:end]
    total_pages = max(1, math.ceil(len(items) / page_size))

    table = Table(
        show_header=True,
        expand=True,
        box=box.SIMPLE,
        header_style=f"bold #FFC107",
        border_style=Theme.muted_text,
    )
    table.add_column("#", style="#FFD700", width=6, no_wrap=True)
    table.add_column("Tool Name", style="bold #FFD700", min_width=30)
    table.add_column("Category", style="#FFC107", min_width=18)

    for tool in page_items:
        fav = "* " if tool.id in favorites else "  "
        num = f"{fav}> {int(tool.id):02d}"
        cat_icon = get_category_icon(tool.category)
        cat_color = get_default_color(tool.category)
        table.add_row(num, tool.name, f"[{cat_color}]{cat_icon}[/]")

    for _ in range(page_size - len(page_items)):
        table.add_row("", "", "")

    return Panel(
        table,
        title=f"[bold #FFC107]TOOLS -- Page {current_page + 1}/{total_pages}[/]",
        border_style="#FFC107",
        box=box.SIMPLE,
    )


def get_page_tools(items, current_page: int = 0, page_size: int = TOOLS_PER_PAGE) -> list:
    start = current_page * page_size
    end = start + page_size
    return items[start:end]


# ─── HELP TABLE ─────────────────────────────────


def make_tools_help_table(items) -> Table:
    table = Table(
        title=Text(f" {TOOL_NAME} v{TOOL_VERSION} -- All Tools ", style=f"bold {Theme.gold1}"),
        border_style=Theme.gold1,
        box=box.SIMPLE,
        header_style=f"bold {Theme.gold2}",
    )
    table.add_column("ID", justify="right", style=Theme.gold1, width=4)
    table.add_column("Tool", style=Theme.gold2)
    table.add_column("Category", style=Theme.amber)
    table.add_column("Description", style=Theme.muted_text)
    for item in items:
        table.add_row(item.id, item.name, item.category, item.desc)
    return table


# ─── INFO PANEL ─────────────────────────────────


def get_info_panel(items, current_page: int = 0, page_size: int = 15, tip: str = "") -> Panel:
    t = Text()
    if tip:
        t.append("  [!] TIP\n", style=f"bold {Theme.gold3}")
        t.append(f"  {tip}\n\n", style=f"{Theme.gold2}")

    t.append(f"  -- COMMANDS --\n", style=Theme.muted_text)
    for key, desc in [
        ("H", "Help"),
        ("Q", "Quit"),
        ("D", "Next Page"),
        ("A", "Prev Page"),
        ("F", "Favorite"),
        ("*", "Favorites"),
        ("T", "Theme"),
        ("/", "Search"),
    ]:
        t.append(f"  [", style=Theme.muted_text)
        t.append(key, style=f"bold {Theme.muted_text}")
        t.append(f"] {desc}\n", style=f"{Theme.gold2}")

    start_num = current_page * page_size + 1
    end_num = min((current_page + 1) * page_size, len(items))
    t.append(f"\n  -- VIEWING --\n", style=Theme.muted_text)
    t.append(f"  Tools {start_num}-{end_num}\n\n", style=f"{Theme.gold2}")

    t.append(f"  -- CATEGORIES --\n", style=Theme.muted_text)
    cats: dict[str, int] = {}
    for item in items:
        cats[item.category] = cats.get(item.category, 0) + 1
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        cat_icon = get_category_icon(cat)
        cc = get_default_color(cat)
        t.append(f"  ", style=Theme.muted_text)
        t.append(cat_icon, style=cc)
        t.append(f"  {count}\n", style=Theme.muted_text)

    return Panel(t, title=Text(" INFO ", style=f"bold {Theme.gold3}"), border_style=Theme.amber)


# ─── NAV INFO (for right panel, shows page-range) ────


def get_nav_info(page: int, total: int) -> Text:
    t = Text(justify="center")
    t.append(f"[ <- A ]  ", style=Theme.muted_text)
    t.append(f"P{page}/{total}", style=f"bold {Theme.gold1}")
    t.append(f"  [ D -> ]", style=Theme.muted_text)
    return t


# ─── FOOTER ─────────────────────────────────────


def get_footer_panel(current_page: int = 1, total_pages: int = 1, tool_count: int = 0) -> Panel:
    t = Text()
    t.append(f"  ## {TOOL_NAME} v{TOOL_VERSION}  ##  ", style=Theme.muted_text)
    t.append(f"Page {current_page}/{total_pages}  ##  ", style=f"bold {Theme.gold1}")
    t.append(f"{tool_count} tools  ##  ", style=Theme.muted_text)
    t.append(f"discord.gg/cheapymarket  ##  ", style=Theme.muted_text)
    t.append(f"made by psixakias.7  ##", style=Theme.muted_text)
    return Panel(t, border_style=Theme.amber, box=box.SIMPLE)


# ─── LAUNCH ANIMATION ──────────────────────────


def launch_tool_animation(tool_name: str):
    os.system('cls')
    console.print(f"\n[bold #FFD700]  +{'='*50}+[/]")
    console.print(f"[bold #FFD700]  |  {'  [*]  CHEAPY TOOL -- LAUNCHING MODULE':^50}|[/]")
    console.print(f"[bold #FFD700]  |{tool_name:^50}|[/]")
    console.print(f"[bold #FFD700]  +{'='*50}+[/]\n")
    bar = ""
    for i in range(30):
        bar += "#"
        spaces = "." * (30 - i - 1)
        pct = int((i + 1) / 30 * 100)
        sys.stdout.write(f"\r  {Fore.YELLOW}{Style.BRIGHT}[{bar}{spaces}] {pct}%{Style.RESET_ALL}")
        sys.stdout.flush()
        _time.sleep(0.03)
    print("\n")


# ─── FULL LAYOUT ────────────────────────────────


def generate_layout(
    items_table: Panel,
    skull_banner: Panel | None = None,
    nav_bar: Panel | None = None,
    info_panel: Panel | None = None,
    header_panel: Panel | None = None,
    footer_panel: Panel | None = None,
) -> Layout:
    HEADER_ROWS = 1
    SKULL_ROWS = 1
    NAV_ROWS = 1
    FOOTER_ROWS = 1

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=HEADER_ROWS),
        Layout(name="skull_banner", size=SKULL_ROWS),
        Layout(name="body"),
        Layout(name="footer", size=FOOTER_ROWS),
    )
    layout["body"].split_row(
        Layout(name="tools", ratio=4),
        Layout(name="info", ratio=1),
    )
    layout["body"]["tools"].split_column(
        Layout(name="nav_bar", size=NAV_ROWS),
        Layout(name="tool_list"),
    )

    if skull_banner:
        layout["skull_banner"].update(skull_banner)
    if nav_bar:
        layout["body"]["tools"]["nav_bar"].update(nav_bar)
    if info_panel:
        layout["body"]["info"].update(info_panel)
    if header_panel:
        layout["header"].update(header_panel)
    if footer_panel:
        layout["footer"].update(footer_panel)
    layout["body"]["tools"]["tool_list"].update(items_table)

    return layout


# ─── ANIMATIONS ─────────────────────────────────


def matrix_rain(duration=1.5):
    cols = min(shutil.get_terminal_size().columns, 100)
    rows = shutil.get_terminal_size().lines
    drops = [0] * cols
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#$%&@"
    end = _time.time() + duration
    with console.screen() as screen:
        while _time.time() < end:
            lines = []
            for y in range(rows):
                line_t = Text()
                for x in range(cols):
                    if y == drops[x] and drops[x] > 0:
                        c = random.choice(chars)
                        clr = random.choice(GOLD_COLORS)
                        line_t.append(c, style=f"bold {clr}")
                    elif 0 < drops[x] - y < 4:
                        c = random.choice(chars)
                        line_t.append(c, style=f"dim {Theme.muted_text}")
                    else:
                        line_t.append(" ")
                lines.append(line_t)
            screen.update(Text("\n").join(lines))
            for i in range(cols):
                if drops[i] <= 0 and random.random() < 0.04:
                    drops[i] = random.randint(rows // 4, rows)
                if drops[i] > 0:
                    drops[i] -= 1
            _time.sleep(0.05)


def golden_progress(duration=0.8, description="Loading"):
    progress = Progress(
        SpinnerColumn(spinner_name="dots", style=Theme.gold2),
        TextColumn(f"[bold {Theme.gold3}]{description}" + " [progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(bar_width=30, style=Theme.muted_text, complete_style=Theme.gold1),
        TimeElapsedColumn(),
        console=console,
    )
    with progress:
        task = progress.add_task("", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            _time.sleep(duration / 100)


def slide_in(rows: list[str], delay=0.02):
    for row in rows:
        t = Text()
        for i, c in enumerate(row):
            t.append(c, style=GOLD_COLORS[i % len(GOLD_COLORS)])
        console.print(t)
        _time.sleep(delay)


def exit_explosion():
    chars = ["*", "*", "*", "*", "*", "*"]
    cols = min(shutil.get_terminal_size().columns, 100)
    rows = shutil.get_terminal_size().lines
    for frame in range(6):
        intensity = 6 - frame
        lines = []
        for _ in range(rows):
            lt = Text()
            for _ in range(cols):
                if random.random() < (intensity / 10):
                    c = random.choice(chars)
                    clr = GOLD_COLORS[frame % len(GOLD_COLORS)]
                    lt.append(c, style=f"bold {clr}")
                else:
                    lt.append(" ")
            lines.append(lt)
        console.print(Text("\n").join(lines))
        _time.sleep(0.06)
    for _ in range(3):
        line = "".join(random.choice(" ..") for _ in range(shutil.get_terminal_size().columns))
        console.print(f"[dim {Theme.muted_text}]{line}[/]")
        _time.sleep(0.1)
    console.print(f"\n  [bold {Theme.gold1}]Thanks for using {TOOL_NAME}![/]")
    _time.sleep(0.5)


# ─── ASCII QR ──────────────────────────────────


def _qr_modules(text: str) -> list[list[bool]]:
    data = text.encode("utf-8")
    size = max(21, (len(data) * 8 + 4) ** 0.5)
    size = int(math.ceil(size / 2) * 2 + 5)
    if size < 21:
        size = 21
    if size % 2 == 0:
        size += 1
    grid = [[False] * size for _ in range(size)]
    for i in range(size):
        grid[0][i] = True; grid[i][0] = True
        grid[size - 1][i] = True; grid[i][size - 1] = True
    for r in range(7):
        for c in range(7):
            if r == 0 or r == 6 or c == 0 or c == 6:
                grid[r][c] = True; grid[r][size - 1 - c] = True
                grid[size - 1 - r][c] = True
            elif 1 < r < 5 and 1 < c < 5:
                grid[r][c] = True; grid[r][size - 1 - c] = True
                grid[size - 1 - r][c] = True
    bit_idx = 0
    for r in range(9, size - 1):
        for c in range(1, size - 1):
            if r == 9 and c < 9: continue
            if r >= size - 8 and c < 8: continue
            if c == size - 8 and r < 8: continue
            if bit_idx < len(data) * 8:
                byte_idx = bit_idx // 8
                bit = (data[byte_idx] >> (7 - (bit_idx % 8))) & 1
                grid[r][c] = bit == 1; bit_idx += 1
    return grid


def ascii_qr(text: str, add_label: bool = True) -> Text:
    grid = _qr_modules(text)
    result = Text()
    for r in range(len(grid)):
        for c in range(len(grid[r])):
            result.append("##" if grid[r][c] else "  ",
                          style=f"bold {Theme.gold1}" if grid[r][c] else Theme.bg)
        result.append("\n")
    if add_label:
        result.append(Text(f"\nQR: {text[:40]}", style=Theme.muted_text))
    return result


# ─── ASCII WORLD MAP ───────────────────────────


ASCII_WORLD_MAP = r"""
[bold #FFB300]                    .-:::::-.                                    
                  .-:::::::::::-.     G R E E N L A N D       
                .:::::::::::::::::.        (DENMARK)          
               ::::::::.    .:::::::                           
              :::::::::      ::::::::                           
       -------:::::::::.  .::::::::-------                     
      ::::::::::::::::::::::::::::::::::::.                    
     ::::::::.    .:::::::::::.    .:::::::                    
    ::::::::        :::::::::        ::::::::                   
   ::::::::.        :::::::::        .:::::::***                
   ::::::::         :::::::::         ::::::***  E U R O P E    
   ::::::::.        :::::::::        .:::::::***                
    ::::::::        :::::::::        ::::::::                   
 [bold #FFD700]A S I A[/]  ::::::::.    .:::::::::::.    .:::::::                    
      ::::::::::::::::::::::::::::::::::::.                    
       -------:::::::::.  .::::::::-------                     
              ::::::::      ::::::::***                         
 [bold #FFB300]A F R I C A[/]  :::::::.    .:::::::***                         
                .:::::::::::::::::::***                         
                  .:::::::::::::::***                           
                    .-:::::::-.***                              
                             ***                                
 A U S T R A L I A          ***  [bold #FFD700]S O U T H[/]                            
                    *****************  [bold #FFD700]A M E R I C A[/]                     
"""


def ascii_ip_map(lat: float, lon: float, city: str = "", country: str = "") -> Text:
    map_lines = ASCII_WORLD_MAP.split("\n")
    result = Text()
    for line in map_lines:
        result.append(line + "\n")
    lat_d = f"{lat:.2f}" if lat else "?"
    lon_d = f"{lon:.2f}" if lon else "?"
    loc = f"{city}, {country}" if city and country else f"{lat_d}, {lon_d}"
    result.append(f"\n  * Location: {loc}\n", style=Theme.gold2)
    result.append(f"  Lat: {lat_d}  Lon: {lon_d}", style=Theme.gold3)
    return result


# ─── SESSION LOGGER ────────────────────────────


class SessionLogger:
    def __init__(self, log_path: str | None = None):
        if log_path is None:
            log_path = str(OUTPUT_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.log_path = log_path
        self.entries: list[str] = []

    def log(self, entry: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {entry}"
        self.entries.append(line)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def get_recent(self, n: int = 5) -> list[str]:
        return [e.split("] ", 1)[-1] if "] " in e else e for e in self.entries[-n:]]


# ─── PAGINATION VERIFICATION ──────────────────


def verify_pagination():
    tools = [{"id": i, "name": f"Tool {i}"} for i in range(1, 55)]
    with open("pagination_check.txt", "w", encoding="utf-8") as f:
        for p in range(math.ceil(54 / TOOLS_PER_PAGE)):
            start = p * TOOLS_PER_PAGE
            end = start + TOOLS_PER_PAGE
            page_tools = tools[start:end]
            ids = [t["id"] for t in page_tools]
            f.write(f"Page {p+1}: tools {ids}\n")


# ─── TOOL OF THE DAY ───────────────────────────


TOOL_TIPS = [
    "Use /search to find any tool instantly!",
    "Press F to favorite a tool, * to view all favorites.",
    "Press T to cycle through gold/silver/bronze/neon themes.",
    "Some tools need admin rights.",
    "Username tracker searches 50+ platforms at once.",
    "Use the Discord admin for advanced server management.",
    "Port scanner supports custom port ranges and service detection.",
    "JWT decoder can inspect tokens without sending them anywhere.",
]

_tool_of_day: str | None = None


def tool_of_the_day() -> str:
    global _tool_of_day
    if _tool_of_day is None:
        random.seed(_time.time())
        _tool_of_day = random.choice(TOOL_TIPS)
    return _tool_of_day
