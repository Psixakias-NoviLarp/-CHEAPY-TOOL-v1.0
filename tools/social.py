from __future__ import annotations

import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import *


class SocialModule:
    def run(self):
        section_header("Social & Roblox Tools")
        console.print()
        menu_items = [
            ("1", "Check YouTube Channel"),
            ("2", "Check X (Twitter) Profile"),
            ("3", "Check TikTok Profile"),
            ("4", "Check Instagram Profile"),
            ("5", "Check Telegram User"),
            ("6", "Check Reddit User"),
            ("7", "Check Twitch Channel"),
            ("8", "Check GitHub User"),
            ("9", "Roblox Profile Lookup"),
            ("10", "Roblox Avatar Info"),
            ("11", "Roblox Inventory"),
            ("12", "Roblox Groups"),
            ("13", "Roblox Badges"),
            ("14", "Roblox Friends"),
            ("15", "Roblox Game Info"),
            ("0", "Back"),
        ]
        table = make_table("Social & Roblox", ["#", "Tool"])
        for num, label in menu_items:
            table.add_row(Text(num, style=Theme.primary), Text(label, style=Theme.secondary))
        console.print(table)

        choice = get_input("Select tool")
        match choice:
            case "0": return
            case "1": self.youtube_lookup()
            case "2": self.x_lookup()
            case "3": self.tiktok_lookup()
            case "4": self.instagram_lookup()
            case "5": self.telegram_lookup()
            case "6": self.reddit_lookup()
            case "7": self.twitch_lookup()
            case "8": self.github_lookup()
            case "9": self.roblox_profile()
            case "10": self.roblox_avatar()
            case "11": self.roblox_inventory()
            case "12": self.roblox_groups()
            case "13": self.roblox_badges()
            case "14": self.roblox_friends()
            case "15": self.roblox_game()
            case _: error("Invalid.")
        pause()

    def _req(self, url: str, timeout: int = 10) -> dict | None:
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def _profile_table(self, data: dict, fields: list) -> None:
        t = make_table("Profile Info", ["Field", "Value"])
        for label, key in fields:
            val = data.get(key, "N/A")
            if isinstance(val, dict):
                val = str(val.get("name", val))
            t.add_row(Text(label, style=Theme.accent), Text(str(val)[:80], style=Theme.secondary))
        console.print(t)

    def youtube_lookup(self):
        handle = get_input("YouTube channel handle (e.g. @channel)")
        url = f"https://www.youtube.com/{handle}"
        info(f"Opening: {url}")
        import webbrowser
        webbrowser.open(url)
        try:
            r = requests.get(f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={handle.replace('@','')}&type=channel&key=", timeout=10)
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items:
                    info(f"Channel: {items[0]['snippet']['title']}")
        except Exception:
            pass

    def x_lookup(self):
        username = get_input("X username")
        import webbrowser
        webbrowser.open(f"https://twitter.com/{username}")
        info(f"Opened: https://twitter.com/{username}")

    def tiktok_lookup(self):
        username = get_input("TikTok username")
        import webbrowser
        webbrowser.open(f"https://tiktok.com/@{username}")
        info(f"Opened: https://tiktok.com/@{username}")

    def instagram_lookup(self):
        username = get_input("Instagram username")
        import webbrowser
        webbrowser.open(f"https://instagram.com/{username}")
        try:
            r = self._req(f"https://www.instagram.com/{username}/?__a=1&__d=1")
            if r:
                user = r.get("graphql", {}).get("user", {})
                self._profile_table(user, [
                    ("Username", "username"), ("Full Name", "full_name"), ("Bio", "biography"),
                    ("Posts", "edge_owner_to_timeline_media", lambda d: d.get("count")),
                    ("Followers", "edge_followed_by", lambda d: d.get("count")),
                    ("Following", "edge_follow", lambda d: d.get("count")),
                    ("Private", "is_private"), ("Verified", "is_verified"),
                ])
        except Exception:
            pass

    def telegram_lookup(self):
        username = get_input("Telegram username")
        import webbrowser
        webbrowser.open(f"https://t.me/{username}")
        info(f"Opened: https://t.me/{username}")

    def reddit_lookup(self):
        username = get_input("Reddit username")
        url = f"https://www.reddit.com/user/{username}/about.json"
        r = self._req(url)
        if r and r.get("data"):
            d = r["data"]
            self._profile_table(d, [
                ("Username", "name"), ("ID", "id"), ("Karma", "total_karma"),
                ("Created", "created_utc"), ("Is Gold", "is_gold"),
                ("Is Employee", "is_employee"), ("Has Verified Email", "has_verified_email"),
                ("Subreddit", "subreddit.display_name_prefixed"),
            ])
        else:
            info(f"Reddit: https://reddit.com/user/{username}")

    def twitch_lookup(self):
        username = get_input("Twitch channel name")
        import webbrowser
        webbrowser.open(f"https://twitch.tv/{username}")
        info(f"Opened: https://twitch.tv/{username}")

    def github_lookup(self):
        username = get_input("GitHub username")
        r = self._req(f"https://api.github.com/users/{username}")
        if r:
            self._profile_table(r, [
                ("Login", "login"), ("Name", "name"), ("Bio", "bio"),
                ("Company", "company"), ("Location", "location"), ("Email", "email"),
                ("Public Repos", "public_repos"), ("Followers", "followers"),
                ("Following", "following"), ("Created", "created_at"),
                ("Type", "type"), ("Hireable", "hireable"),
            ])
        else:
            info(f"GitHub: https://github.com/{username}")

    # ─── ROBLOX ─────────────────────────────────
    def _uid_input(self) -> int | None:
        val = get_input("Roblox username or user ID")
        if val.isdigit():
            return int(val)
        try:
            r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [val], "excludeBannedUsers": False}, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    return data[0].get("id")
        except Exception:
            pass
        error("User not found.")
        return None

    def roblox_profile(self):
        uid = self._uid_input()
        if not uid:
            return
        r = self._req(f"https://users.roblox.com/v1/users/{uid}")
        if r:
            pres = self._req(f"https://presence.roblox.com/v1/presence/users", timeout=10)
            pres_status = "Unknown"
            if pres:
                for u in pres.json().get("userPresences", []):
                    if u.get("user-id") == uid:
                        pres_status = {0: "Offline", 1: "Online", 2: "In Game", 3: "Studio"}.get(u.get("userPresenceType", 0), "Unknown")
            t = make_table("Roblox Profile", ["Field", "Value"])
            t.add_row(Text("Username", style=Theme.accent), Text(r.get("name", "N/A"), style=Theme.secondary))
            t.add_row(Text("Display Name", style=Theme.accent), Text(r.get("displayName", "N/A"), style=Theme.secondary))
            t.add_row(Text("ID", style=Theme.accent), Text(str(uid), style=Theme.secondary))
            t.add_row(Text("Description", style=Theme.accent), Text((r.get("description") or "N/A")[:80], style=Theme.secondary))
            t.add_row(Text("Created", style=Theme.accent), Text(str(r.get("created", "N/A"))[:19], style=Theme.secondary))
            t.add_row(Text("Online", style=Theme.accent), Text(pres_status, style=Theme.success if pres_status not in ("Offline", "Unknown") else Theme.muted))
            t.add_row(Text("Banned", style=Theme.accent), Text(str(r.get("isBanned", False)), style=Theme.secondary))
            console.print(t)
            prof_url = f"https://www.roblox.com/users/{uid}/profile"
            info(f"Profile: {prof_url}")
        pause()

    def roblox_avatar(self):
        uid = self._uid_input()
        if not uid:
            return
        r = self._req(f"https://avatar.roblox.com/v1/users/{uid}/avatar")
        if r:
            t = make_table("Avatar Info", ["Field", "Value"])
            t.add_row(Text("Body Type", style=Theme.accent), Text(str(r.get("bodyType", 0)), style=Theme.secondary))
            t.add_row(Text("Scale", style=Theme.accent), Text(str(r.get("scale", {})), style=Theme.secondary))
            asset_ids = r.get("assetIds", [])
            t.add_row(Text("Worn Items", style=Theme.accent), Text(str(len(asset_ids)), style=Theme.secondary))
            console.print(t)
            if asset_ids:
                info(f"Item IDs: {', '.join(str(a) for a in asset_ids[:20])}")
        pause()

    def roblox_inventory(self):
        uid = self._uid_input()
        if not uid:
            return
        asset_type = get_input("Asset type ID (8=hat, 2=tshirt, 11=pants, 41=gear). Leave blank for all", "")
        url = f"https://inventory.roblox.com/v1/users/{uid}/assets/collectibles"
        r = self._req(url)
        if r and r.get("data"):
            t = make_table("Inventory", ["Name", "Asset ID", "Recent Average Price"])
            for item in r["data"][:30]:
                t.add_row(Text(item.get("name", "?")[:30], style=Theme.secondary), Text(str(item.get("assetId", "?")), style=Theme.muted), Text(f"R${item.get('recentAveragePrice', 0):,}", style=Theme.accent))
            console.print(t)
            info(f"Total collectibles: {r.json().get('total')}")
        else:
            info("No collectibles or private inventory.")

        # Also do standard inventory
        r2 = self._req(f"https://inventory.roblox.com/v1/users/{uid}/assets/standard")
        if r2:
            info(f"Standard items: {r2.json().get('total', 0)}")
        pause()

    def roblox_groups(self):
        uid = self._uid_input()
        if not uid:
            return
        r = self._req(f"https://groups.roblox.com/v1/users/{uid}/groups/roles")
        if r and r.get("data"):
            t = make_table("Groups", ["Name", "ID", "Rank", "Role"])
            for g in r["data"]:
                group = g.get("group", {})
                role = g.get("role", {})
                t.add_row(Text(group.get("name", "?")[:30], style=Theme.secondary), Text(str(group.get("id", "?")), style=Theme.muted), Text(f"{role.get('rank', 0)}", style=Theme.accent), Text(role.get("name", "?"), style=Theme.secondary))
            console.print(t)
        pause()

    def roblox_badges(self):
        uid = self._uid_input()
        if not uid:
            return
        r = self._req(f"https://badges.roblox.com/v1/users/{uid}/badges?limit=30")
        if r and r.get("data"):
            t = make_table("Badges", ["Name", "ID", "Description"])
            for b in r["data"]:
                t.add_row(Text(b.get("name", "?")[:30], style=Theme.secondary), Text(str(b.get("id", "?")), style=Theme.muted), Text((b.get("description") or "")[:40], style=Theme.secondary))
            console.print(t)
        pause()

    def roblox_friends(self):
        uid = self._uid_input()
        if not uid:
            return
        r = self._req(f"https://friends.roblox.com/v1/users/{uid}/friends")
        if r and r.get("data"):
            t = make_table("Friends", ["Username", "ID", "Online"])
            for f in r["data"][:50]:
                t.add_row(Text(f.get("name", "?")[:20], style=Theme.secondary), Text(str(f.get("id", "?")), style=Theme.muted), Text(str(f.get("isOnline", False)), style=Theme.accent))
            console.print(t)
            info(f"Showing {min(50, len(r['data']))} friends")
        pause()

    def roblox_game(self):
        game_id = get_input("Roblox game/place ID or URL")
        if "roblox.com" in game_id:
            import re as _re
            m = _re.search(r"(\d+)", game_id)
            if m:
                game_id = m.group(1)
        if not game_id.isdigit():
            error_then_exit("Invalid game ID.")
        r = self._req(f"https://games.roblox.com/v1/games?universeIds={game_id}")
        if r and r.get("data"):
            g = r["data"][0]
            t = make_table("Game Info", ["Field", "Value"])
            t.add_row(Text("Name", style=Theme.accent), Text(g.get("name", "N/A"), style=Theme.secondary))
            t.add_row(Text("Description", style=Theme.accent), Text((g.get("description") or "N/A")[:80], style=Theme.secondary))
            t.add_row(Text("Creator", style=Theme.accent), Text(g.get("creator", {}).get("name", "N/A"), style=Theme.secondary))
            t.add_row(Text("Price", style=Theme.accent), Text(f"{g.get('price', 0):,}" if g.get("price") else "Free", style=Theme.secondary))
            t.add_row(Text("Visits", style=Theme.accent), Text(f"{g.get('visits', 0):,}", style=Theme.secondary))
            t.add_row(Text("Favorites", style=Theme.accent), Text(f"{g.get('favoritedCount', 0):,}", style=Theme.secondary))
            t.add_row(Text("Max Players", style=Theme.accent), Text(str(g.get("maxPlayers", 0)), style=Theme.secondary))
            t.add_row(Text("Created", style=Theme.accent), Text(str(g.get("created", "N/A"))[:19], style=Theme.secondary))
            t.add_row(Text("Updated", style=Theme.accent), Text(str(g.get("updated", "N/A"))[:19], style=Theme.secondary))
            console.print(t)
        else:
            r2 = self._req(f"https://games.roblox.com/v1/games/multiget-place-details?placeIds={game_id}")
            if r2:
                data = r2[0] if isinstance(r2, list) else r2
                t = make_table("Place Info", ["Field", "Value"])
                t.add_row(Text("Name", style=Theme.accent), Text(data.get("Name", "N/A"), style=Theme.secondary))
                t.add_row(Text("Visits", style=Theme.accent), Text(f"{data.get('Visits', 0):,}", style=Theme.secondary))
                t.add_row(Text("Favorites", style=Theme.accent), Text(f"{data.get('Favorited', 0):,}", style=Theme.secondary))
                console.print(t)
        pause()
