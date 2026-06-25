from __future__ import annotations

import sys
import requests
from pathlib import Path
from rich.table import Table
from rich.text import Text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import *


class DiscordAdminModule:
    API = "https://discord.com/api/v9"

    def run(self):
        section_header("Discord Server Admin CLI")
        console.print(Text("39+ server management commands — for authorized use only", style=Theme.warning))
        console.print()

        token = get_input("Bot token (preferred) or user token")
        prefix = "Bot " if len(token) < 50 else ""
        headers = {"Authorization": f"{prefix}{token}", "Content-Type": "application/json"}
        guild_id = get_input("Server (Guild) ID")

        # Verify access
        r = requests.get(f"{self.API}/guilds/{guild_id}", headers=headers, timeout=10)
        if r.status_code != 200:
            error_then_exit(f"Cannot access server (HTTP {r.status_code}). Check token & permissions.")

        guild_name = r.json().get("name", "Unknown")
        info(f"Connected to: {guild_name} ({guild_id})")
        console.print()

        while True:
            menu_items = [
                ("1", "Server Info"),          ("2", "List Channels"),
                ("3", "Create Channel"),        ("4", "Delete Channel"),
                ("5", "Clone Channel"),         ("6", "Edit Channel Name"),
                ("7", "List Roles"),            ("8", "Create Role"),
                ("9", "Delete Role"),           ("10", "List Members"),
                ("11", "Ban Member"),           ("12", "Unban Member"),
                ("13", "Kick Member"),          ("14", "Mute Member"),
                ("15", "Deafen Member"),        ("16", "Member Info"),
                ("17", "List Bans"),            ("18", "List Invites"),
                ("19", "Create Invite"),        ("20", "Purge Messages"),
                ("21", "Get Channel Messages"), ("22", "List Emojis"),
                ("23", "Create Emoji"),         ("24", "Delete Emoji"),
                ("25", "List Stickers"),        ("26", "Add Role to User"),
                ("27", "Remove Role from User"),("28", "List Webhooks"),
                ("29", "Create Webhook"),       ("30", "Server Audit Log"),
                ("31", "Server Widget"),        ("32", "Vanity URL Info"),
                ("33", "Server Boosts"),        ("34", "Timeout User"),
                ("35", "Remove Timeout"),       ("36", "Move All to VC"),
                ("37", "Disconnect All from VC"),("38", "Nickname All"),
                ("39", "Mass Role Assign"),     ("0", "Back"),
            ]

            table = Table(title=Text(f"Admin: {guild_name}", style=Theme.primary), border_style=Theme.primary, header_style=f"bold {Theme.secondary}", show_lines=True)
            table.add_column("#", style=Theme.primary, width=4)
            table.add_column("Command", style=Theme.secondary, width=22)
            table.add_column("#", style=Theme.primary, width=4)
            table.add_column("Command", style=Theme.secondary, width=22)
            half = (len(menu_items) + 1) // 2
            for i in range(half):
                left = menu_items[i] if i < len(menu_items) else ("", "", "")
                right = menu_items[i + half] if i + half < len(menu_items) else ("", "", "")
                table.add_row(left[0], left[1], right[0], right[1])
            console.print(table)

            choice = get_input("Command #")
            try:
                match choice:
                    case "0": break
                    case "1": self.server_info(headers, guild_id)
                    case "2": self.list_channels(headers, guild_id)
                    case "3": self.create_channel(headers, guild_id)
                    case "4": self.delete_channel(headers, guild_id)
                    case "5": self.clone_channel(headers, guild_id)
                    case "6": self.edit_channel(headers, guild_id)
                    case "7": self.list_roles(headers, guild_id)
                    case "8": self.create_role(headers, guild_id)
                    case "9": self.delete_role(headers, guild_id)
                    case "10": self.list_members(headers, guild_id)
                    case "11": self.ban_member(headers, guild_id)
                    case "12": self.unban_member(headers, guild_id)
                    case "13": self.kick_member(headers, guild_id)
                    case "14": self.mute_member(headers, guild_id)
                    case "15": self.deafen_member(headers, guild_id)
                    case "16": self.member_info(headers, guild_id)
                    case "17": self.list_bans(headers, guild_id)
                    case "18": self.list_invites(headers, guild_id)
                    case "19": self.create_invite(headers, guild_id)
                    case "20": self.purge_messages(headers, guild_id)
                    case "21": self.get_messages(headers, guild_id)
                    case "22": self.list_emojis(headers, guild_id)
                    case "23": self.create_emoji(headers, guild_id)
                    case "24": self.delete_emoji(headers, guild_id)
                    case "25": self.list_stickers(headers, guild_id)
                    case "26": self.add_role(headers, guild_id)
                    case "27": self.remove_role(headers, guild_id)
                    case "28": self.list_webhooks(headers, guild_id)
                    case "29": self.create_webhook(headers, guild_id)
                    case "30": self.audit_log(headers, guild_id)
                    case "31": self.server_widget(headers, guild_id)
                    case "32": self.vanity_url(headers, guild_id)
                    case "33": self.server_boosts(headers, guild_id)
                    case "34": self.timeout_user(headers, guild_id)
                    case "35": self.remove_timeout(headers, guild_id)
                    case "36": self.move_all_vc(headers, guild_id)
                    case "37": self.disconnect_vc(headers, guild_id)
                    case "38": self.nickname_all(headers, guild_id)
                    case "39": self.mass_role_assign(headers, guild_id)
                    case _: error("Invalid.")
            except Exception as e:
                error(f"Error: {e}")

    def _get(self, headers, url):
        return requests.get(url, headers=headers, timeout=10)

    def _post(self, headers, url, json=None):
        return requests.post(url, headers=headers, json=json or {}, timeout=10)

    def _patch(self, headers, url, json=None):
        return requests.patch(url, headers=headers, json=json or {}, timeout=10)

    def _delete(self, headers, url):
        return requests.delete(url, headers=headers, timeout=10)

    def _put(self, headers, url, json=None):
        return requests.put(url, headers=headers, json=json or {}, timeout=10)

    def _channel_id(self, guild_id, headers, name_hint="") -> str:
        if name_hint:
            r = self._get(headers, f"{self.API}/guilds/{guild_id}/channels")
            if r.status_code == 200:
                for ch in r.json():
                    if name_hint.lower() in ch["name"].lower():
                        return ch["id"]
        return get_input("Channel ID")

    def server_info(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}?with_counts=true")
        if r.status_code == 200:
            g = r.json()
            t = make_table("Server Info", ["Field", "Value"])
            for k in ("name", "id", "owner_id", "region", "premium_tier", "premium_subscription_count", "member_count", "description", "nsfw_level", "explicit_content_filter", "mfa_level", "verification_level"):
                t.add_row(Text(k, style=Theme.accent), Text(str(g.get(k, "N/A")), style=Theme.secondary))
            t.add_row(Text("Channels", style=Theme.accent), str(len(g.get("channels", []))))
            t.add_row(Text("Roles", style=Theme.accent), str(len(g.get("roles", []))))
            console.print(t)
        pause()

    def list_channels(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/channels")
        if r.status_code == 200:
            channels = sorted(r.json(), key=lambda c: (c.get("type", 0), c.get("position", 0)))
            t = make_table("Channels", ["Type", "Name", "ID", "Topic"])
            for ch in channels:
                type_map = {0: "Text", 2: "Voice", 4: "Category", 5: "Announcement", 13: "Stage"}
                ch_type = type_map.get(ch.get("type", 0), "?")
                t.add_row(Text(ch_type, style=Theme.accent), Text(ch["name"], style=Theme.secondary), Text(ch["id"], style=Theme.muted), Text((ch.get("topic") or "")[:30], style=Theme.secondary))
            console.print(t)
        pause()

    def create_channel(self, headers, guild_id):
        name = get_input("Channel name")
        ch_type = get_input("Type (text/voice/category)", "text")
        type_map = {"text": 0, "voice": 2, "category": 4, "announcement": 5}
        r = self._post(headers, f"{self.API}/guilds/{guild_id}/channels", {"name": name, "type": type_map.get(ch_type, 0)})
        if r.status_code in (200, 201):
            success(f"Channel created: {r.json().get('name')} ({r.json().get('id')})")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def delete_channel(self, headers, guild_id):
        cid = get_input("Channel ID")
        if not confirm(f"DELETE channel {cid}?"):
            return
        r = self._delete(headers, f"{self.API}/channels/{cid}")
        if r.status_code == 200:
            success("Channel deleted.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def clone_channel(self, headers, guild_id):
        cid = get_input("Channel ID to clone")
        r = self._get(headers, f"{self.API}/channels/{cid}")
        if r.status_code != 200:
            error("Could not fetch channel.")
            pause()
            return
        ch = r.json()
        name = ch.get("name", "cloned") + "-clone"
        data = {k: ch[k] for k in ("name", "type", "topic", "nsfw", "rate_limit_per_user", "position") if k in ch}
        data["name"] = name
        r2 = self._post(headers, f"{self.API}/guilds/{guild_id}/channels", data)
        if r2.status_code in (200, 201):
            success(f"Cloned: {name}")
        else:
            error(f"HTTP {r2.status_code}")
        pause()

    def edit_channel(self, headers, guild_id):
        cid = get_input("Channel ID")
        name = get_input("New name")
        topic = get_input("New topic (optional)")
        data = {"name": name}
        if topic:
            data["topic"] = topic
        r = self._patch(headers, f"{self.API}/channels/{cid}", data)
        if r.status_code == 200:
            success("Channel updated.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def list_roles(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/roles")
        if r.status_code == 200:
            roles = sorted(r.json(), key=lambda x: x.get("position", 0), reverse=True)
            t = make_table("Roles", ["Name", "ID", "Color", "Perms", "Mentionable"])
            for role in roles[:50]:
                t.add_row(Text(role["name"], style=Theme.secondary), Text(role["id"], style=Theme.muted), str(role.get("color", 0)), str(len(role.get("permissions", ""))), str(role.get("mentionable")))
            console.print(t)
        pause()

    def create_role(self, headers, guild_id):
        name = get_input("Role name")
        r = self._post(headers, f"{self.API}/guilds/{guild_id}/roles", {"name": name})
        if r.status_code == 200:
            success(f"Role created: {name} ({r.json().get('id')})")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def delete_role(self, headers, guild_id):
        rid = get_input("Role ID")
        if not confirm(f"DELETE role {rid}?"):
            return
        r = self._delete(headers, f"{self.API}/guilds/{guild_id}/roles/{rid}")
        if r.status_code == 204:
            success("Role deleted.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def list_members(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/members?limit=1000")
        if r.status_code == 200:
            members = r.json()
            t = make_table("Members", ["User", "ID", "Roles", "Joined"])
            for m in members[:100]:
                user = m.get("user", {})
                name = f"{user.get('username', '?')}#{user.get('discriminator', '?')}"
                t.add_row(Text(name, style=Theme.secondary), Text(user.get("id", "?"), style=Theme.muted), str(len(m.get("roles", []))), str(m.get("joined_at", "")[:10]))
            console.print(t)
            info(f"Showing {min(100, len(members))}/{len(members)} members")
        pause()

    def ban_member(self, headers, guild_id):
        uid = get_input("User ID")
        reason = get_input("Reason (optional)")
        r = self._put(headers, f"{self.API}/guilds/{guild_id}/bans/{uid}", {"reason": reason or "Banned via Cheapy Tool"})
        if r.status_code == 204:
            success(f"Banned {uid}")
        elif r.status_code == 200:
            success(f"Banned {uid}")
        else:
            error(f"HTTP {r.status_code}: {r.text[:100]}")
        pause()

    def unban_member(self, headers, guild_id):
        uid = get_input("User ID to unban")
        r = self._delete(headers, f"{self.API}/guilds/{guild_id}/bans/{uid}")
        if r.status_code == 204:
            success(f"Unbanned {uid}")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def kick_member(self, headers, guild_id):
        uid = get_input("User ID to kick")
        if not confirm(f"KICK {uid}?"):
            return
        r = self._delete(headers, f"{self.API}/guilds/{guild_id}/members/{uid}")
        if r.status_code == 204:
            success(f"Kicked {uid}")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def mute_member(self, headers, guild_id):
        uid = get_input("User ID")
        r = self._patch(headers, f"{self.API}/guilds/{guild_id}/members/{uid}", {"mute": True})
        if r.status_code == 200:
            success(f"Muted {uid}")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def deafen_member(self, headers, guild_id):
        uid = get_input("User ID")
        r = self._patch(headers, f"{self.API}/guilds/{guild_id}/members/{uid}", {"deaf": True})
        if r.status_code == 200:
            success(f"Deafened {uid}")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def member_info(self, headers, guild_id):
        uid = get_input("User ID")
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/members/{uid}")
        if r.status_code == 200:
            m = r.json()
            user = m.get("user", {})
            t = make_table("Member Info", ["Field", "Value"])
            t.add_row(Text("Username", style=Theme.accent), Text(f"{user.get('username')}#{user.get('discriminator')}", style=Theme.secondary))
            t.add_row(Text("ID", style=Theme.accent), Text(user.get("id", ""), style=Theme.secondary))
            t.add_row(Text("Joined", style=Theme.accent), Text(str(m.get("joined_at", "")), style=Theme.secondary))
            t.add_row(Text("Roles", style=Theme.accent), Text(str(len(m.get("roles", []))), style=Theme.secondary))
            t.add_row(Text("Nick", style=Theme.accent), Text(str(m.get("nick", "None")), style=Theme.secondary))
            t.add_row(Text("Timeout", style=Theme.accent), Text(str(m.get("communication_disabled_until", "None")), style=Theme.secondary))
            console.print(t)
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def list_bans(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/bans")
        if r.status_code == 200:
            bans = r.json()
            t = make_table("Bans", ["User", "ID", "Reason"])
            for b in bans:
                u = b.get("user", {})
                t.add_row(Text(f"{u.get('username')}#{u.get('discriminator')}", style=Theme.secondary), Text(u.get("id", ""), style=Theme.muted), Text((b.get("reason") or "None")[:40], style=Theme.secondary))
            console.print(t)
            info(f"Total bans: {len(bans)}")
        pause()

    def list_invites(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/invites")
        if r.status_code == 200:
            t = make_table("Invites", ["Code", "Channel", "Uses", "Max", "Creator", "Expires"])
            for inv in r.json()[:50]:
                t.add_row(Text(inv["code"], style=Theme.accent), Text(inv.get("channel", {}).get("name", "?"), style=Theme.secondary), str(inv.get("uses", 0)), str(inv.get("max_uses", 0)), Text(inv.get("inviter", {}).get("username", "?") if inv.get("inviter") else "?", style=Theme.muted), str(inv.get("max_age", 0)))
            console.print(t)
        pause()

    def create_invite(self, headers, guild_id):
        cid = self._channel_id(guild_id, headers)
        max_age = int(get_input("Max age (seconds, 0=never)", "86400"))
        max_uses = int(get_input("Max uses (0=unlimited)", "0"))
        r = self._post(headers, f"{self.API}/channels/{cid}/invites", {"max_age": max_age, "max_uses": max_uses, "temporary": False})
        if r.status_code == 200:
            success(f"Invite: https://discord.gg/{r.json().get('code')}")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def purge_messages(self, headers, guild_id):
        cid = get_input("Channel ID")
        limit = int(get_input("Messages to fetch & delete", "50"))
        if not confirm(f"DELETE up to {limit} messages in {cid}?"):
            return
        deleted = 0
        while limit > 0:
            batch = min(limit, 100)
            try:
                r = requests.get(f"{self.API}/channels/{cid}/messages?limit={batch}", headers=headers, timeout=10)
                if r.status_code != 200:
                    break
                msgs = r.json()
                if not msgs:
                    break
                ids = [m["id"] for m in msgs]
                if len(ids) == 1:
                    self._delete(headers, f"{self.API}/channels/{cid}/messages/{ids[0]}")
                else:
                    r2 = requests.post(f"{self.API}/channels/{cid}/messages/bulk-delete", headers=headers, json={"messages": ids}, timeout=10)
                    if r2.status_code not in (200, 204):
                        break
                deleted += len(ids)
                limit -= len(ids)
            except Exception as e:
                error(f"Purge: {e}")
                break
        success(f"Deleted {deleted} messages.")
        pause()

    def get_messages(self, headers, guild_id):
        cid = get_input("Channel ID")
        limit = int(get_input("Count", "20"))
        r = self._get(headers, f"{self.API}/channels/{cid}/messages?limit={min(limit, 100)}")
        if r.status_code == 200:
            t = make_table("Messages", ["Author", "Content", "ID"])
            for msg in r.json():
                author = msg.get("author", {}).get("username", "?")
                content = (msg.get("content", "") or "")[:50]
                t.add_row(Text(author, style=Theme.accent), Text(content, style=Theme.secondary), Text(msg["id"], style=Theme.muted))
            console.print(t)
        pause()

    def list_emojis(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/emojis")
        if r.status_code == 200:
            t = make_table("Emojis", ["Name", "ID", "Animated", "Managed"])
            for e in r.json():
                t.add_row(Text(f":{e['name']}:", style=Theme.secondary), Text(e["id"], style=Theme.muted), str(e.get("animated", False)), str(e.get("managed", False)))
            console.print(t)
        pause()

    def create_emoji(self, headers, guild_id):
        name = get_input("Emoji name")
        img_url = get_input("Image URL")
        r_img = requests.get(img_url, timeout=10)
        if r_img.status_code != 200:
            error("Could not fetch image.")
            pause()
            return
        import base64
        b64 = base64.b64encode(r_img.content).decode()
        r = self._post(headers, f"{self.API}/guilds/{guild_id}/emojis", {"name": name, "image": f"data:image/png;base64,{b64}"})
        if r.status_code == 201:
            success(f"Emoji :{name}: created!")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def delete_emoji(self, headers, guild_id):
        eid = get_input("Emoji ID")
        if not confirm("DELETE this emoji?"):
            return
        r = self._delete(headers, f"{self.API}/guilds/{guild_id}/emojis/{eid}")
        if r.status_code == 204:
            success("Emoji deleted.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def list_stickers(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/stickers")
        if r.status_code == 200:
            t = make_table("Stickers", ["Name", "ID", "Type", "Tags"])
            for s in r.json():
                t.add_row(Text(s.get("name", "?"), style=Theme.secondary), Text(s.get("id", "?"), style=Theme.muted), str(s.get("type", 0)), Text(s.get("tags", ""), style=Theme.secondary))
            console.print(t)
        pause()

    def add_role(self, headers, guild_id):
        uid = get_input("User ID")
        rid = get_input("Role ID")
        r = self._put(headers, f"{self.API}/guilds/{guild_id}/members/{uid}/roles/{rid}")
        if r.status_code == 204:
            success("Role added.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def remove_role(self, headers, guild_id):
        uid = get_input("User ID")
        rid = get_input("Role ID")
        r = self._delete(headers, f"{self.API}/guilds/{guild_id}/members/{uid}/roles/{rid}")
        if r.status_code == 204:
            success("Role removed.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def list_webhooks(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/webhooks")
        if r.status_code == 200:
            t = make_table("Webhooks", ["Name", "ID", "Channel", "Token"])
            for wh in r.json():
                t.add_row(Text(wh.get("name", "?"), style=Theme.secondary), Text(wh.get("id", "?"), style=Theme.muted), Text(wh.get("channel_id", "?"), style=Theme.secondary), Text((wh.get("token") or "???")[:20] + "...", style=Theme.muted))
            console.print(t)
        pause()

    def create_webhook(self, headers, guild_id):
        cid = self._channel_id(guild_id, headers)
        name = get_input("Webhook name")
        r = self._post(headers, f"{self.API}/channels/{cid}/webhooks", {"name": name})
        if r.status_code in (200, 201):
            wh = r.json()
            url = f"https://discord.com/api/v9/webhooks/{wh['id']}/{wh['token']}"
            success(f"Webhook created: {url}")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def audit_log(self, headers, guild_id):
        limit = int(get_input("Entries to fetch", "20"))
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/audit-logs?limit={min(limit, 100)}")
        if r.status_code == 200:
            logs = r.json().get("audit_log_entries", [])
            users = {u["id"]: u["username"] for u in r.json().get("users", [])}
            t = make_table("Audit Log", ["User", "Action", "Target", "ID"])
            action_map = {1: "Update", 10: "Create", 11: "Create", 12: "Create", 20: "Delete", 21: "Delete", 22: "Delete", 30: "Kick", 31: "Ban", 40: "Timeout"}
            for entry in logs[:50]:
                uid = entry.get("user_id", "")
                username = users.get(uid, uid[:8])
                action = action_map.get(entry.get("action_type", 0), str(entry.get("action_type", 0)))
                target = entry.get("target_id", "N/A")[:15]
                t.add_row(Text(username, style=Theme.secondary), Text(action, style=Theme.accent), Text(target, style=Theme.muted), Text(entry["id"][:8], style=Theme.muted))
            console.print(t)
        pause()

    def server_widget(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/widget")
        if r.status_code == 200:
            w = r.json()
            t = make_table("Widget", ["Field", "Value"])
            t.add_row(Text("Enabled", style=Theme.accent), str(w.get("enabled", False)))
            t.add_row(Text("Channel", style=Theme.accent), Text(str(w.get("channel_id", "N/A")), style=Theme.secondary))
            t.add_row(Text("Invite", style=Theme.accent), Text(str(w.get("instant_invite", "N/A")), style=Theme.secondary))
            console.print(t)
        pause()

    def vanity_url(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/vanity-url")
        if r.status_code == 200:
            code = r.json().get("code")
            if code:
                success(f"Vanity URL: https://discord.gg/{code}")
            else:
                info("No vanity URL set.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def server_boosts(self, headers, guild_id):
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/premium/subscriptions")
        if r.status_code == 200:
            boosts = r.json()
            info(f"Total boosts: {len(boosts)}")
            t = make_table("Boosts", ["User", "Tier", "Started"])
            for b in boosts[:30]:
                user = b.get("user", {})
                name = f"{user.get('username', '?')}#{user.get('discriminator', '?')}" if user else "?"
                t.add_row(Text(name, style=Theme.secondary), str(b.get("tier", 0)), Text(str(b.get("created_at", ""))[:10], style=Theme.muted))
            console.print(t)
        pause()

    def timeout_user(self, headers, guild_id):
        uid = get_input("User ID")
        minutes = int(get_input("Duration (minutes)", "60"))
        import datetime
        until = (datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)).isoformat()
        r = self._patch(headers, f"{self.API}/guilds/{guild_id}/members/{uid}", {"communication_disabled_until": until})
        if r.status_code == 200:
            success(f"Timed out {uid} for {minutes} minutes.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def remove_timeout(self, headers, guild_id):
        uid = get_input("User ID")
        r = self._patch(headers, f"{self.API}/guilds/{guild_id}/members/{uid}", {"communication_disabled_until": None})
        if r.status_code == 200:
            success(f"Timeout removed from {uid}.")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def move_all_vc(self, headers, guild_id):
        from_cid = get_input("Source voice channel ID")
        to_cid = get_input("Target voice channel ID")
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/members?limit=1000")
        if r.status_code == 200:
            moved = 0
            for m in r.json():
                if m.get("voice", {}).get("channel_id") == from_cid:
                    uid = m.get("user", {}).get("id")
                    self._patch(headers, f"{self.API}/guilds/{guild_id}/members/{uid}", {"channel_id": to_cid})
                    moved += 1
            success(f"Moved {moved} members.")
        pause()

    def disconnect_vc(self, headers, guild_id):
        cid = get_input("Voice channel ID to disconnect all from")
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/members?limit=1000")
        if r.status_code == 200:
            disc = 0
            for m in r.json():
                if m.get("voice", {}).get("channel_id") == cid:
                    uid = m.get("user", {}).get("id")
                    self._patch(headers, f"{self.API}/guilds/{guild_id}/members/{uid}", {"channel_id": None})
                    disc += 1
            success(f"Disconnected {disc} members.")
        pause()

    def nickname_all(self, headers, guild_id):
        nick = get_input("New nickname for all members")
        if not confirm(f"Change ALL member nicknames to '{nick}'?"):
            return
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/members?limit=1000")
        if r.status_code == 200:
            changed = 0
            for m in r.json():
                uid = m.get("user", {}).get("id")
                if uid:
                    r2 = self._patch(headers, f"{self.API}/guilds/{guild_id}/members/{uid}", {"nick": nick})
                    if r2.status_code == 200:
                        changed += 1
            success(f"Changed nicknames for {changed} members.")
        pause()

    def mass_role_assign(self, headers, guild_id):
        rid = get_input("Role ID to assign")
        if not confirm(f"Assign this role to ALL current members?"):
            return
        r = self._get(headers, f"{self.API}/guilds/{guild_id}/members?limit=1000")
        if r.status_code == 200:
            assigned = 0
            for m in r.json():
                uid = m.get("user", {}).get("id")
                if uid:
                    r2 = self._put(headers, f"{self.API}/guilds/{guild_id}/members/{uid}/roles/{rid}")
                    if r2.status_code == 204:
                        assigned += 1
            success(f"Assigned role to {assigned} members.")
        pause()
