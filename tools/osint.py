from __future__ import annotations

import json
import random
import re
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, quote

import phonenumbers
from phonenumbers import carrier, geocoder, timezone as pn_timezone
import requests
import dns.resolver

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import *


class OsintModule:
    """Combined OSINT tools from all three projects."""

    # ──────────────────────────────────────────────
    #  IP Lookup (ip-api.com)
    # ──────────────────────────────────────────────
    def ip_lookup(self):
        ip = get_input("IP address")
        timeout_val = get_input("Timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        wait_msg(f"Looking up {ip}...")
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=timeout)
            if r.status_code != 200:
                error_then_exit("API returned an error.")
            data = r.json()
            if data.get("status") == "fail":
                error_then_exit(f"Invalid IP: {data.get('message', 'unknown error')}")

            section_header("IP Information")
            table = make_table("Field", "Value")
            fields = [
                ("IP", "query"), ("Country", "country"), ("Region", "regionName"),
                ("City", "city"), ("ZIP", "zip"), ("Latitude", "lat"),
                ("Longitude", "lon"), ("ISP", "isp"), ("Organization", "org"),
                ("AS", "as"), ("Timezone", "timezone"), ("Mobile", "mobile"),
                ("Proxy", "proxy"), ("Hosting", "hosting"),
            ]
            for label, key in fields:
                val = data.get(key)
                if val is not None and val != "":
                    table.add_row(Text(label, style=Theme.accent), Text(str(val), style=Theme.secondary))
            console.print(table)

            # Google Maps link
            lat, lon = data.get("lat"), data.get("lon")
            if lat and lon:
                maps = f"https://www.google.com/maps?q={lat},{lon}"
                info(f"Google Maps: {maps}")

        except requests.exceptions.Timeout:
            error_then_exit("API request timed out.")
        except requests.exceptions.RequestException as e:
            error_then_exit(f"Request error: {e}")
        pause()

    # ──────────────────────────────────────────────
    #  Phone Number Lookup
    # ──────────────────────────────────────────────
    def phone_lookup(self):
        phone = get_input("Phone number (with country code, e.g. +33612345678)")
        try:
            num = phonenumbers.parse(phone)
        except phonenumbers.NumberParseException:
            error_then_exit("Invalid phone number format.")

        section_header("Phone Number Information")
        table = make_table("Property", "Value")
        table.add_row(Text("Number", style=Theme.accent), Text(phone, style=Theme.secondary))
        table.add_row(Text("Valid", style=Theme.accent), str(phonenumbers.is_valid_number(num)))
        table.add_row(Text("Possible", style=Theme.accent), str(phonenumbers.is_possible_number(num)))
        table.add_row(Text("Country", style=Theme.accent), str(geocoder.description_for_number(num, "en")))
        table.add_row(Text("Location", style=Theme.accent), str(geocoder.description_for_valid_number(num, "en") or "N/A"))
        table.add_row(Text("Carrier", style=Theme.accent), str(carrier.name_for_number(num, "en") or "N/A"))
        table.add_row(Text("Timezone", style=Theme.accent), ", ".join(pn_timezone.time_zones_for_number(num)) or "N/A")
        table.add_row(Text("Type", style=Theme.accent), str(phonenumbers.number_type(num)))
        table.add_row(Text("Format (E164)", style=Theme.accent), phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164))
        table.add_row(Text("Format (National)", style=Theme.accent), phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.NATIONAL))
        table.add_row(Text("Format (International)", style=Theme.accent), phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        console.print(table)
        pause()

    # ──────────────────────────────────────────────
    #  Email Lookup (MX/SPF/DMARC)
    # ──────────────────────────────────────────────
    def email_lookup(self):
        email = get_input("Email address")

        import re as _re
        if not _re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error_then_exit("Invalid email format.")

        domain = email.split("@")[1]
        timeout_val = get_input("Timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        section_header(f"Email: {email}")

        table = make_table("Record", "Value")

        # MX records
        try:
            mx = dns.resolver.resolve(domain, "MX", lifetime=timeout)
            for rdata in mx:
                table.add_row(Text("MX", style=Theme.accent), Text(f"{rdata.exchange} (priority {rdata.preference})", style=Theme.secondary))
        except Exception:
            table.add_row(Text("MX", style=Theme.accent), "No MX records found")

        # SPF (TXT)
        spf_found = False
        try:
            txt = dns.resolver.resolve(domain, "TXT", lifetime=timeout)
            for rdata in txt:
                txt_str = str(rdata)
                if txt_str.startswith("v=spf1"):
                    table.add_row(Text("SPF", style=Theme.accent), Text(txt_str[:80], style=Theme.secondary))
                    spf_found = True
        except Exception:
            pass
        if not spf_found:
            table.add_row(Text("SPF", style=Theme.accent), "No SPF record found")

        # DMARC
        try:
            dmarc = dns.resolver.resolve(f"_dmarc.{domain}", "TXT", lifetime=timeout)
            for rdata in dmarc:
                table.add_row(Text("DMARC", style=Theme.accent), Text(str(rdata)[:80], style=Theme.secondary))
        except Exception:
            table.add_row(Text("DMARC", style=Theme.accent), "No DMARC record found")

        # A records
        try:
            a = dns.resolver.resolve(domain, "A", lifetime=timeout)
            ips = [str(r) for r in a]
            table.add_row(Text("A Records", style=Theme.accent), Text(", ".join(ips[:5]), style=Theme.secondary))
        except Exception:
            pass

        console.print(table)

        # Breach check (simplified - via haveibeenpwned API)
        wait_msg("Checking for known breaches...")
        try:
            r = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}", timeout=timeout, headers={"hibp-api-key": ""})
            if r.status_code == 200:
                breaches = r.json()
                warning(f"Found in {len(breaches)} breach(es)!")
                for b in breaches[:10]:
                    console.print(f"  [{Theme.error}]-[/] {b['Name']} ({b.get('BreachDate', 'unknown')})")
                if len(breaches) > 10:
                    info(f"... and {len(breaches) - 10} more")
            elif r.status_code == 404:
                info("No known breaches found.")
            else:
                info("Breach check unavailable (rate limited).")
        except Exception:
            info("Breach check unavailable.")

        pause()

    # ──────────────────────────────────────────────
    #  Username Tracker (60+ platforms)
    # ──────────────────────────────────────────────
    def username_tracker(self):
        username = get_input("Username to search")
        timeout_val = get_input("Timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

        platforms = USERNAME_PLATFORMS if USERNAME_PLATFORMS else {
            "GitHub": {"url": "https://github.com/%USERNAME%", "check": "status"},
            "Twitter": {"url": "https://twitter.com/%USERNAME%", "check": "status"},
            "Instagram": {"url": "https://instagram.com/%USERNAME%", "check": "status"},
            "Reddit": {"url": "https://reddit.com/user/%USERNAME%", "check": "status"},
            "YouTube": {"url": "https://youtube.com/@%USERNAME%", "check": "status"},
            "Telegram": {"url": "https://t.me/%USERNAME%", "check": "status"},
            "Twitch": {"url": "https://twitch.tv/%USERNAME%", "check": "status"},
            "TikTok": {"url": "https://tiktok.com/@%USERNAME%", "check": "status"},
            "Pinterest": {"url": "https://pinterest.com/%USERNAME%", "check": "status"},
            "Medium": {"url": "https://medium.com/@%USERNAME%", "check": "status"},
            "Dev.to": {"url": "https://dev.to/%USERNAME%", "check": "status"},
            "Replit": {"url": "https://replit.com/@%USERNAME%", "check": "status"},
            "GitLab": {"url": "https://gitlab.com/%USERNAME%", "check": "status"},
            "Bitbucket": {"url": "https://bitbucket.org/%USERNAME%", "check": "status"},
            "Keybase": {"url": "https://keybase.io/%USERNAME%", "check": "status"},
            "Snapchat": {"url": "https://snapchat.com/add/%USERNAME%", "check": "status"},
            "Steam": {"url": "https://steamcommunity.com/id/%USERNAME%", "check": "status"},
            "Spotify": {"url": "https://open.spotify.com/user/%USERNAME%", "check": "text", "text": "Page not found"},
            "Discord": {"url": "https://discord.com/users/%USERNAME%", "check": "status"},
            "Facebook": {"url": "https://facebook.com/%USERNAME%", "check": "status"},
            "Dribbble": {"url": "https://dribbble.com/%USERNAME%", "check": "status"},
            "Behance": {"url": "https://behance.net/%USERNAME%", "check": "status"},
            "SoundCloud": {"url": "https://soundcloud.com/%USERNAME%", "check": "status"},
            "Flickr": {"url": "https://flickr.com/people/%USERNAME%", "check": "status"},
            "Vimeo": {"url": "https://vimeo.com/%USERNAME%", "check": "status"},
            "DeviantArt": {"url": "https://deviantart.com/%USERNAME%", "check": "status"},
            "AngelList": {"url": "https://angel.co/u/%USERNAME%", "check": "status"},
            "ProductHunt": {"url": "https://producthunt.com/@%USERNAME%", "check": "status"},
            "HackerNews": {"url": "https://news.ycombinator.com/user?id=%USERNAME%", "check": "status"},
            "BuyMeACoffee": {"url": "https://buymeacoffee.com/%USERNAME%", "check": "status"},
            "Patreon": {"url": "https://patreon.com/%USERNAME%", "check": "status"},
            "Trello": {"url": "https://trello.com/%USERNAME%", "check": "status"},
        }

        from rich.progress import Progress, SpinnerColumn, TextColumn

        found: list[tuple[str, str]] = []
        progress = Progress(SpinnerColumn(), TextColumn("{task.description}"))
        task = progress.add_task(f"Scanning {len(platforms)} platforms...", total=len(platforms))

        with progress:
            for name, pdata in platforms.items():
                url = pdata["url"].replace("%USERNAME%", username)
                try:
                    r = session.get(url, timeout=timeout, allow_redirects=True)
                    check = pdata.get("check", "status")
                    if check == "status" and r.status_code == 200:
                        found.append((name, url))
                        success(f"{name}: {url}")
                    elif check == "text":
                        not_found_text = pdata.get("text", "not found")
                        if not_found_text.lower() not in r.text.lower() and r.status_code == 200:
                            found.append((name, url))
                            success(f"{name}: {url}")
                        else:
                            warning(f"{name}: Not found")
                    else:
                        warning(f"{name}: Not found")
                except Exception:
                    warning(f"{name}: Error")
                progress.update(task, advance=1)

        if found:
            section_header(f"Found on {len(found)}/{len(platforms)} platforms")
            table = make_table("Platform", "URL")
            for name, url in found:
                table.add_row(Text(name, style=Theme.success), Text(url, style=Theme.secondary))
            console.print(table)
        else:
            warning("No platforms matched.")
        pause()

    # ──────────────────────────────────────────────
    #  Dorking Query Engine
    # ──────────────────────────────────────────────
    def dorking_engine(self):
        engines = {
            "1": ("Google", "https://www.google.com/search?q="),
            "2": ("Bing", "https://www.bing.com/search?q="),
            "3": ("DuckDuckGo", "https://duckduckgo.com/?q="),
        }

        console.print(make_table("Search Engines", ["#", "Engine", "URL"]))
        for k, (name, url) in engines.items():
            console.print(f"  [{Theme.primary}]{k}[/]  {name:<12} {url}")

        choice = get_input("Select engine")
        if choice not in engines:
            error_then_exit("Invalid choice.")
        engine_name, engine_url = engines[choice]

        operators: dict[str, list[str]] = {}
        match engine_name:
            case "Google":
                operators = {
                    "1": "inurl:", "2": "intitle:", "3": "site:", "4": '""',
                    "5": "-", "6": "filetype:", "7": "intext:", "8": "OR",
                    "9": "()", "10": "..", "11": "AROUND()", "12": "define:",
                    "13": "*", "14": "after:", "15": "before:",
                }
            case "Bing":
                operators = {
                    "1": "inurl:", "2": "intitle:", "3": "site:", "4": '""',
                    "5": "-", "6": "filetype:", "7": "OR", "8": "()",
                    "9": "..", "10": "define:", "11": "*",
                }
            case "DuckDuckGo":
                operators = {
                    "1": "site:", "2": '""', "3": "-", "4": "OR",
                    "5": "()", "6": "define:", "7": "*",
                }

        info(f"Operators for {engine_name}:")
        table = make_table("#", "Operator")
        for k, op in operators.items():
            table.add_row(Text(k, style=Theme.primary), Text(op, style=Theme.accent))
        console.print(table)

        query_parts: list[str] = []
        while True:
            op_choice = get_input("Select operator (0 to finish)")
            if op_choice == "0" or op_choice == "":
                break
            if op_choice in operators:
                val = get_input("Value")
                op_str = operators[op_choice]
                if op_str == '""':
                    query_parts.append(f'"{val}"')
                elif op_str in ("OR",):
                    query_parts.append(val.upper())
                elif op_str == "()":
                    query_parts.append(f"({val})")
                elif op_str in ("*",):
                    query_parts.append(f"*{val}*")
                else:
                    query_parts.append(f"{op_str}{val}")
            else:
                error("Invalid operator.")

        if not query_parts:
            error_then_exit("No query built.")

        query = " ".join(query_parts)
        encoded = quote(query)
        final_url = engine_url + encoded

        info(f"Query: {query}")
        info(f"URL: {final_url}")

        if confirm("Open in browser?"):
            webbrowser.open(final_url)
            info("Browser opened.")
        pause()

    # ──────────────────────────────────────────────
    #  Wallet Tracker
    # ──────────────────────────────────────────────
    def wallet_tracker(self):
        address = get_input("Crypto wallet address (BTC/ETH)")
        timeout_val = get_input("Timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        # BTC
        if address.startswith(("1", "3", "bc1")):
            url = f"https://blockchain.info/rawaddr/{address}"
            explorer = "https://blockchain.info/address/"
        elif address.startswith(("0x")):
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey=YourApiKeyToken"
            explorer = "https://etherscan.io/address/"
        else:
            error_then_exit("Unsupported wallet format.")

        wait_msg(f"Looking up {address}...")
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                section_header("Wallet Information")
                if "hash160" in data:  # BTC
                    table = make_table("Field", "Value")
                    table.add_row(Text("Address", style=Theme.accent), Text(address, style=Theme.secondary))
                    table.add_row(Text("Total Received", style=Theme.accent), f"{data.get('total_received', 0) / 1e8:.8f} BTC")
                    table.add_row(Text("Total Sent", style=Theme.accent), f"{data.get('total_sent', 0) / 1e8:.8f} BTC")
                    table.add_row(Text("Final Balance", style=Theme.accent), f"{data.get('final_balance', 0) / 1e8:.8f} BTC")
                    table.add_row(Text("Transactions", style=Theme.accent), str(data.get("n_tx", 0)))
                    console.print(table)
                elif data.get("status") == "1":  # ETH
                    txns = data.get("result", [])
                    info(f"Found {len(txns)} transactions")
                    table = make_table("Tx", "From", "To", "Value (ETH)", "Hash")
                    for tx in txns[:20]:
                        val = int(tx.get("value", 0)) / 1e18
                        table.add_row(
                            Text(tx.get("hash", "")[:10] + "...", style=Theme.primary),
                            Text(tx.get("from", "")[:10] + "...", style=Theme.secondary),
                            Text(tx.get("to", "")[:10] + "...", style=Theme.secondary),
                            f"{val:.6f}",
                            Text(tx.get("hash", "")[:10] + "...", style=Theme.muted),
                        )
                    console.print(table)
                info(f"Explorer: {explorer}{address}")
            else:
                error("API error.")
        except Exception as e:
            error(f"Error: {e}")
        pause()

    # ──────────────────────────────────────────────
    #  Instagram Profile Lookup
    # ──────────────────────────────────────────────
    def instagram_lookup(self):
        username = get_input("Instagram username")
        session_id = get_input("Instagram session id (optional)")

        if session_id:
            cookies = {"sessionid": session_id}
        else:
            cookies = {}

        url = f"https://www.instagram.com/{username}/?__a=1&__d=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }

        wait_msg(f"Looking up {username}...")
        try:
            r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
            if r.status_code == 200:
                data = r.json()
                user = data.get("graphql", {}).get("user", data.get("user", {})) or data
                section_header("Instagram Profile")
                table = make_table("Field", "Value")
                fields = [
                    ("Username", "username"), ("Full Name", "full_name"), ("Bio", "biography"),
                    ("Posts", "edge_owner_to_timeline_media", lambda d: d.get("count") if isinstance(d, dict) else d),
                    ("Followers", "edge_followed_by", lambda d: d.get("count") if isinstance(d, dict) else d),
                    ("Following", "edge_follow", lambda d: d.get("count") if isinstance(d, dict) else d),
                    ("Private", "is_private"), ("Verified", "is_verified"),
                    ("Business", "is_business_account"), ("ID", "id"),
                ]
                for label, key, *transform in fields:
                    val = user.get(key, "N/A")
                    if transform and callable(transform[0]):
                        try:
                            val = transform[0](val)
                        except Exception:
                            pass
                    table.add_row(Text(label, style=Theme.accent), Text(str(val), style=Theme.secondary))
                console.print(table)
            elif r.status_code == 404:
                error("Profile not found.")
            else:
                error(f"HTTP {r.status_code}. Login may be required.")
        except Exception as e:
            error(f"Error: {e}")
        pause()
