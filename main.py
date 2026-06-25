# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import io

os.system("chcp 65001 >nul")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

os.system("title Cheapy Tool v1.0")

import colorama
colorama.init()

import math as _math
import sys as _sys
import time as _time
from pathlib import Path
from typing import Callable

_sys.path.insert(0, str(Path(__file__).parent.resolve()))

from rich.panel import Panel
from rich.text import Text

from config import *
from ui import *

from tools.network import NetworkModule
from tools.osint import OsintModule
from tools.discord import DiscordModule
from tools.utils import UtilitiesModule, WebhookToolkitModule
from tools.system import AnonymizerModule, CleanerModule
from tools.admin import DiscordAdminModule
from tools.social import SocialModule
from tools.gen import GeneratorsModule, ExtraModule
from tools.web import IpWebExtendedModule


class MenuItem:
    def __init__(self, id: str, name: str, desc: str, category: str, func: Callable, icon: str = ""):
        self.id = id
        self.name = name
        self.desc = desc
        self.category = category
        self.func = func
        self.icon = icon


class CheapyApp:
    def __init__(self):
        self.network = NetworkModule()
        self.osint = OsintModule()
        self.discord = DiscordModule()
        self.utilities = UtilitiesModule()
        self.anonymizer = AnonymizerModule()
        self.cleaner = CleanerModule()
        self.webhook_tk = WebhookToolkitModule()
        self.discord_admin = DiscordAdminModule()
        self.social = SocialModule()
        self.generators = GeneratorsModule()
        self.ip_web = IpWebExtendedModule()
        self.extra = ExtraModule()
        self.config = Config()
        self.session = SessionLogger()
        self.current_theme = "gold"
        self.favorites: set[str] = set()
        self.recent_tools: list[str] = []
        self.theme_colors = dict(COLOR_THEMES["gold"])

        self.current_page = 0
        self.show_help = False
        self.show_favorites = False
        self.in_tool = False
        self.running = True

        self._build_menu()

    def _build_menu(self):
        self.items: list[MenuItem] = [
            MenuItem("1",  "Advanced Scanner",     "Full target scan (IP DNS WHOIS ports HTTP)",                    "Network", self.network.advanced_scan),
            MenuItem("2",  "Port Scanner",          "TCP/UDP port scanning with service detection",                  "Network", self.network.port_scan),
            MenuItem("3",  "Vulnerability Scanner", "Web vulnerability scanner SQLi XSS SSTI",                       "Network", self.network.vuln_scan),
            MenuItem("4",  "URL Discovery",         "Crawl and discover website URLs",                               "Network", self.network.url_discovery),
            MenuItem("5",  "IP Pinger",             "ICMP/TCP ping with live stats",                                 "Network", self.network.ip_pinger),
            MenuItem("6",  "Host Discovery",        "Discover live hosts on a network CIDR",                         "Network", self.network.host_discovery),
            MenuItem("7",  "IP Lookup",             "Geolocation and ISP data via ip-api.com",                       "OSINT",   self.osint.ip_lookup),
            MenuItem("8",  "Phone Lookup",          "Phone number carrier location and validation",                  "OSINT",   self.osint.phone_lookup),
            MenuItem("9",  "Email Lookup",          "Email validation MX SPF DMARC and breach check",                "OSINT",   self.osint.email_lookup),
            MenuItem("10", "Username Tracker",      "Search username across 50+ platforms",                          "OSINT",   self.osint.username_tracker),
            MenuItem("11", "Dorking Engine",        "Google Bing DuckDuckGo dork query builder",                    "OSINT",   self.osint.dorking_engine),
            MenuItem("12", "Wallet Tracker",        "Track BTC ETH wallet transactions",                             "OSINT",   self.osint.wallet_tracker),
            MenuItem("13", "Instagram Lookup",      "Instagram profile data",                                       "OSINT",   self.osint.instagram_lookup),
            MenuItem("14", "Token Info",            "Full Discord token information",                                "Discord", self.discord.token_info),
            MenuItem("15", "Token Checker",         "Multi-threaded Discord token validator",                        "Discord", self.discord.token_checker),
            MenuItem("16", "DM All",                "Mass DM to friends open DMs or server members",                 "Discord", self.discord.dm_all),
            MenuItem("17", "Token Nuker",           "Nuke Discord account leave guilds remove friends",              "Discord", self.discord.token_nuker),
            MenuItem("18", "Token Raid",            "Channel raid with multi-threading",                             "Discord", self.discord.token_raid),
            MenuItem("19", "Webhook Tools",         "Webhook info and spammer basic",                                "Discord", self.discord.webhook_tools),
            MenuItem("20", "Nitro Generator",       "Discord Nitro code generator and checker",                      "Discord", self.discord.nitro_generator),
            MenuItem("21", "Metadata Scanner",      "Extract EXIF/metadata from files",                              "Utils",   self.utilities.metadata_scanner),
            MenuItem("22", "Metadata Deleter",      "Remove EXIF/metadata from files",                               "Utils",   self.utilities.metadata_deleter),
            MenuItem("23", "Website Cloner",        "Clone entire websites locally",                                 "Utils",   self.utilities.website_cloner),
            MenuItem("24", "SQL Vuln Scanner",      "SQL injection vulnerability scanner",                           "Utils",   self.utilities.sql_vuln_scanner),
            MenuItem("25", "Windows Anonymizer",    "Disable telemetry Cortana bloat location tracking",             "System",  self.anonymizer.run),
            MenuItem("26", "System Cleaner",        "CCleaner-like temp files caches logs recycle bin",              "System",  self.cleaner.run_all),
            MenuItem("27", "Webhook Toolkit",       "19 webhook tools spam embed clone rotator",                     "Webhook", self.webhook_tk.run),
            MenuItem("28", "Discord Server Admin",  "39+ server commands roles bans purge",                          "Admin",   self.discord_admin.run),
            MenuItem("29", "Social and Roblox",     "YouTube X TikTok Insta Telegram Roblox profile",                "Social",  self.social.run),
            MenuItem("30", "Generators",            "Hash password Base64 QR UUID JWT temp mail cracker",            "Gen",     self.generators.run),
            MenuItem("31", "IP and Web Extended",   "Subdomain dir discovery SSL tech detect traceroute DNS",        "Web",     self.ip_web.run),
            MenuItem("32", "IP Geo Map",            "ASCII world map with IP geolocation marker",                    "OSINT",   self.extra.ip_geo_map),
            MenuItem("33", "ASCII QR Generator",    "Generate ASCII QR codes in gold terminal",                      "Gen",     self.extra.ascii_qr_gen),
            MenuItem("34", "Password Strength",     "Test password strength and entropy",                            "Gen",     self.extra.password_strength),
            MenuItem("35", "Hash Cracker",          "MD5 SHA1 SHA256 hash cracking via online lookup",               "Gen",     self.extra.hash_cracker),
            MenuItem("36", "Hex Encoder/Decoder",   "Encode decode text to/from hexadecimal",                       "Gen",     self.extra.hex_tool),
            MenuItem("37", "JWT Token Decoder",     "Decode and inspect JWT tokens",                                 "Gen",     self.extra.jwt_decoder),
            MenuItem("38", "Fake Identity Gen",     "Generate realistic fake identities",                            "Utils",   self.extra.fake_identity),
            MenuItem("39", "Proxy Scraper",         "Scrape and check HTTP HTTPS SOCKS proxies",                    "Network", self.extra.proxy_scraper),
            MenuItem("40", "Port Banner Grabber",   "Grab service banners from open ports",                         "Network", self.extra.banner_grabber),
            MenuItem("41", "API Key Validator",     "Validate common API key formats 30+ services",                  "Utils",   self.extra.api_key_validator),
            MenuItem("42", "MAC Address Lookup",    "Lookup MAC address vendor manufacturer",                       "Network", self.extra.mac_lookup),
            MenuItem("43", "IP Reputation Check",   "Check IP against blacklists and abuse databases",              "OSINT",   self.extra.ip_reputation),
            MenuItem("44", "Hash Identifier",       "Identify hash type from hash string",                          "Gen",     self.extra.hash_identifier),
            MenuItem("45", "File Hasher",           "Hash files with MD5 SHA1 SHA256",                              "Utils",   self.extra.file_hasher),
            MenuItem("46", "ZIP Password Cracker",  "Brute force password protected ZIP files",                     "Utils",   self.extra.zip_cracker),
            MenuItem("47", "Python Obfuscator",     "Basic Python script obfuscation",                              "Utils",   self.extra.python_obfuscator),
            MenuItem("48", "Discord Token Gen",     "Generate Discord token-like strings",                          "Discord", self.extra.discord_token_gen),
            MenuItem("49", "Discord Token Joiner",  "Join a Discord server with a token",                           "Discord", self.extra.discord_token_joiner),
            MenuItem("50", "Discord Bot Nuker",     "Nuke a Discord server with a bot token",                       "Discord", self.extra.discord_bot_nuker),
            MenuItem("51", "Discord Server Cloner", "Clone a Discord server channels roles settings",              "Admin",   self.extra.discord_server_cloner),
            MenuItem("52", "Discord Injection Cln", "Clean Discord token injection from browser",                   "Discord", self.extra.discord_injection_cleaner),
            MenuItem("53", "Stealer Builder",       "Build info stealer (educational only)",                        "Utils",   self.extra.stealer_builder),
            MenuItem("54", "Dox Creator",           "Generate detailed dox with metadata",                          "OSINT",   self.extra.dox_creator),
        ]

    def total_pages(self) -> int:
        return max(1, _math.ceil(len(self.items) / TOOLS_PER_PAGE))

    def _startup_sequence(self):
        import time as _time2
        from colorama import Fore, Style

        os.system("cls")
        print_banner()

        total = 40
        print()
        for i in range(total + 1):
            filled = "=" * i
            empty = "-" * (total - i)
            pct = int(i / total * 100)
            sys.stdout.write(f"\r  {Fore.YELLOW}Loading [{filled}{empty}] {pct}%{Style.RESET_ALL}")
            sys.stdout.flush()
            _time2.sleep(0.04)
        print()

        print(f"\n  {Fore.YELLOW}{Style.BRIGHT}[*] {TOOL_NAME} v{TOOL_VERSION} ready{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{len(self.items)} tools loaded | [H] Help | [D/A] Pages | [Q] Quit{Style.RESET_ALL}")
        print(f"\n  {Fore.YELLOW}Press ENTER to continue...{Style.RESET_ALL}")
        input()
        os.system("cls")

    def _cycle_theme(self):
        themes = list(COLOR_THEMES.keys())
        idx = themes.index(self.current_theme)
        self.current_theme = themes[(idx + 1) % len(themes)]
        colors = COLOR_THEMES[self.current_theme]
        self.theme_colors = dict(colors)
        Theme.gold1 = colors["p"]
        Theme.gold2 = colors["s"]
        Theme.amber = colors["a"]
        Theme.muted_text = colors["m"]
        Theme.bg = colors["bg"]

    def _search_tools(self, query: str) -> list[MenuItem]:
        q = query.lower()
        return [i for i in self.items
                if q in i.name.lower() or q in i.desc.lower() or q in i.category.lower()]

    def _build_layout(self) -> Layout:
        header_panel = make_header_panel()
        skull_banner = get_skull_banner()
        total = self.total_pages()
        nav_bar = get_nav_bar(self.current_page + 1, total)
        tip = tool_of_the_day()
        info_panel = get_info_panel(
            self.items, self.current_page, TOOLS_PER_PAGE,
            tip=tip,
        )
        footer_panel = get_footer_panel(self.current_page + 1, total, len(self.items))

        if self.show_help:
            content = make_tools_help_table(self.items)
            items_panel = Panel(content, border_style=Theme.amber, box=box.SIMPLE,
                                title=Text(" HELP -- All Tools ", style=f"bold {Theme.gold1}"))
        elif self.show_favorites:
            favs = [i for i in self.items if i.id in self.favorites]
            if favs:
                items_panel = get_tools_table(favs, 0, len(favs), self.favorites)
            else:
                self.show_favorites = False
                items_panel = get_tools_table(self.items, self.current_page, TOOLS_PER_PAGE, self.favorites)
        else:
            items_panel = get_tools_table(self.items, self.current_page, TOOLS_PER_PAGE, self.favorites)

        return generate_layout(
            items_table=items_panel,
            skull_banner=skull_banner,
            nav_bar=nav_bar,
            info_panel=info_panel,
            header_panel=header_panel,
            footer_panel=footer_panel,
        )

    def _run_tool(self, item: MenuItem):
        self.in_tool = True
        try:
            beep(600, 50)
            launch_tool_animation(item.name)
            self.recent_tools.append(item.name)
            if len(self.recent_tools) > 20:
                self.recent_tools = self.recent_tools[-20:]
            self.session.log(f"Launched: {item.name}")
            item.func()
        except KeyboardInterrupt:
            warning("Cancelled.")
            self.session.log(f"Cancelled: {item.name}")
        except Exception as e:
            styled_error_box(f"{item.name}: {e}")
            self.session.log(f"Error: {item.name}: {e}")
        finally:
            console.print()
            self.in_tool = False

        console.print("\n[bold #FFD700]" + "-" * 46 + "[/]")
        console.print("[bold #FFD700]  [+] Tool finished -- returning to menu  [/]")
        console.print("[bold #FFD700]" + "-" * 46 + "[/]")
        console.print("\n[#FFC107]  Press ENTER to continue...[/]")
        input()

    def _process_command(self, cmd: str):
        if not cmd:
            return
        if cmd.upper() == 'Q':
            self.running = False
        elif cmd.upper() == 'D':
            if self.current_page < self.total_pages() - 1:
                self.current_page += 1
        elif cmd.upper() == 'A':
            if self.current_page > 0:
                self.current_page -= 1
        elif cmd.isdigit():
            tool_num = int(cmd)
            item = next((i for i in self.items if i.id == str(tool_num)), None)
            if item:
                self._run_tool(item)
            else:
                console.print(f"[bold red]  +-- ERROR --+[/]")
                console.print(f"[bold red]  |  Tool #{tool_num} not found.  |[/]")
                console.print(f"[bold red]  |  Valid range: 1-54      |[/]")
                console.print(f"[bold red]  +-------------+[/]")
                _time.sleep(1.5)
        elif cmd.startswith('/'):
            search_term = cmd[1:]
            results = self._search_tools(search_term)
            if results:
                console.print(f"\n[bold #FFD700]  Search results for '{search_term}':[/]")
                for r in results:
                    console.print(f"  [{r.id:>2}] {r.name}  [dim]{r.category}[/]")
            else:
                console.print(f"\n  No tools matching '{search_term}'.")
            console.print("\n[#FFC107]  Press ENTER to continue...[/]")
            input()
        elif cmd.upper() == 'H':
            self.show_help = not self.show_help
            self.show_favorites = False
        elif cmd.upper() == 'F':
            if self.recent_tools:
                last = self.recent_tools[-1]
                item = next((i for i in self.items if i.name == last), None)
                if item:
                    if item.id in self.favorites:
                        self.favorites.discard(item.id)
                    else:
                        self.favorites.add(item.id)
        elif cmd.upper() == '*':
            self.show_favorites = not self.show_favorites
            self.show_help = False
            if self.show_favorites and not self.favorites:
                self.show_favorites = False
        elif cmd.upper() == 'T':
            self._cycle_theme()

    def run(self):
        try:
            verify_pagination()
            startup_animation()
            self._startup_sequence()

            while self.running:
                os.system('cls')
                console.print(self._build_layout())

                console.print("[bold #FFD700]+" + "-" * 60 + "+[/]")
                console.print("[bold #FFD700]|  root@cheapy:~#[/] ", end="")

                try:
                    cmd = input().strip()
                except (KeyboardInterrupt, EOFError):
                    break
                console.print("[bold #FFD700]+" + "-" * 60 + "+[/]")

                self._process_command(cmd)

        except Exception as e:
            styled_error_box(f"Unexpected: {e}")
        finally:
            self._exit()

    def _exit(self):
        self.session.log("Session ended")
        beep(600, 100)
        _time.sleep(0.1)
        beep(400, 200)
        exit_explosion()
        warning("Goodbye!")
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
        _sys.exit(0)


def main():
    app = CheapyApp()
    app.run()


if __name__ == "__main__":
    main()
