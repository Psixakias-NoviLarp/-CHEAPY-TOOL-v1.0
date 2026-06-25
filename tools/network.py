from __future__ import annotations

import ipaddress
import json
import random
import socket
import ssl
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import dns.resolver
import requests
import urllib3
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NetworkModule:
    """Combined network/pentesting tools from all three projects."""

    # ──────────────────────────────────────────────
    #  Port Scanner (TCP, UDP, service detection)
    # ──────────────────────────────────────────────
    def port_scan(self):
        target = get_input("Target IP")
        if target in BLACKLIST_IPS:
            error_then_exit("Blocked target.")

        try:
            ipaddress.ip_address(target)
        except ValueError:
            error_then_exit("Invalid IP address.")

        port_input = get_input("Ports (single/ranges e.g. 22,80,1-1000,default,all)", "default")
        protocol = get_input("Protocol (TCP/UDP/TCP,UDP)", "TCP")

        timeout_val = get_input("Socket timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        ports_to_scan: list[int] = []
        match port_input.lower():
            case "all":
                ports_to_scan = list(range(1, 1025))
            case "default":
                ports_to_scan = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9000, 27017]
            case _:
                for part in port_input.replace(" ", "").split(","):
                    if "-" in part:
                        try:
                            s, e = map(int, part.split("-"))
                            ports_to_scan.extend(range(max(1, s), min(e, MAX_PORT) + 1))
                        except ValueError:
                            pass
                    else:
                        try:
                            p = int(part)
                            if 1 <= p <= MAX_PORT:
                                ports_to_scan.append(p)
                        except ValueError:
                            pass

        ports_to_scan = sorted(set(ports_to_scan))
        if not ports_to_scan:
            error_then_exit("No valid ports specified.")

        info(f"Scanning {len(ports_to_scan)} ports on {target} ({protocol})...")

        open_ports: list[int] = []
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        )

        tcp = "TCP" in protocol.upper()
        udp = "UDP" in protocol.upper()

        def _scan_tcp_port(p: int) -> int | None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                result = s.connect_ex((target, p))
                s.close()
                return p if result == 0 else None
            except Exception:
                return None

        def _scan_udp_port(p: int) -> int | None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(timeout)
                s.sendto(b"", (target, p))
                try:
                    s.recvfrom(1024)
                    return p
                except socket.timeout:
                    return None
                finally:
                    s.close()
            except Exception:
                return None

        task = progress.add_task(f"[{Theme.primary}]Scanning ports...", total=len(ports_to_scan))
        with progress:
            with ThreadPoolExecutor(max_workers=100) as pool:
                futs = {}
                for p in ports_to_scan:
                    if tcp:
                        futs[pool.submit(_scan_tcp_port, p)] = ("TCP", p)
                    if udp and p in [53, 67, 68, 123, 137, 138, 161, 162, 500, 514, 520]:
                        futs[pool.submit(_scan_udp_port, p)] = ("UDP", p)

                for fut in as_completed(futs):
                    proto, port = futs[fut]
                    if fut.result():
                        if port not in open_ports:
                            open_ports.append(port)
                            success(f"[{proto}] Port {port} open")
                    progress.update(task, advance=1)

        if not open_ports:
            warning("No open ports found.")
        else:
            info(f"Found {len(open_ports)} open ports")
            table = make_table("Open Ports", ["Port", "Protocol", "Service"])
            for p in sorted(open_ports):
                svc = PORTS.get(str(p), {}).get("service", "unknown") if PORTS else "unknown"
                table.add_row(str(p), protocol, svc)
            console.print(table)

        pause()

    # ──────────────────────────────────────────────
    #  Advanced Scanner (IP, DNS, WHOIS, HTTP, GeoIP)
    # ──────────────────────────────────────────────
    def advanced_scan(self):
        target = get_input("Target (IP/domain/URL)")
        timeout_val = get_input("HTTP timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        wait_msg(f"Running advanced scan on {target}...")
        results: dict[str, Any] = {}

        # GeoIP
        try:
            r = requests.get(f"http://ip-api.com/json/{target}", timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success":
                    results["geoip"] = {
                        "ip": data.get("query"),
                        "country": data.get("country"),
                        "city": data.get("city"),
                        "region": data.get("regionName"),
                        "zip": data.get("zip"),
                        "isp": data.get("isp"),
                        "org": data.get("org"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "timezone": data.get("timezone"),
                    }
        except Exception:
            pass

        # DNS
        dns_info: dict[str, Any] = {}
        for qtype in ("A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"):
            try:
                answers = dns.resolver.resolve(target, qtype, lifetime=timeout)
                dns_info[qtype] = [str(a) for a in answers]
            except Exception:
                dns_info[qtype] = []
        if any(dns_info.values()):
            results["dns"] = dns_info

        # WHOIS (simplified)
        try:
            import whois
            w = whois.whois(target)
            results["whois"] = {
                "registrar": w.registrar,
                "creation": str(w.creation_date) if w.creation_date else None,
                "expiration": str(w.expiration_date) if w.expiration_date else None,
                "name": w.name,
                "org": w.org,
                "country": w.country,
                "emails": w.emails if isinstance(w.emails, list) else [w.emails] if w.emails else [],
            }
        except Exception:
            pass

        # HTTP headers
        try:
            if not target.startswith("http"):
                target_url = f"https://{target}"
            else:
                target_url = target
            r = requests.get(target_url, timeout=timeout, verify=False, allow_redirects=True)
            results["http"] = {
                "status": r.status_code,
                "server": r.headers.get("Server"),
                "tech": r.headers.get("X-Powered-By"),
                "content_type": r.headers.get("Content-Type"),
                "headers": dict(r.headers),
            }
        except Exception:
            pass

        section_header("Advanced Scan Results")
        table = make_table("Category", "Field", "Value")
        for category, data in results.items():
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, list):
                        v = ", ".join(str(x) for x in v[:5])
                    table.add_row(Text(category, style=Theme.primary), Text(k, style=Theme.accent), Text(str(v)[:80], style=Theme.secondary))
        console.print(table)
        pause()

    # ──────────────────────────────────────────────
    #  Vulnerability Scanner
    # ──────────────────────────────────────────────
    def vuln_scan(self):
        target = get_input("Target URL")
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        timeout_val = get_input("HTTP timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        cookie = get_input("Cookie (optional)")
        user_agent = get_input("User-Agent (or 'random')", "CheapyTool/1.0")

        if user_agent.lower() == "random":
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})
        session.verify = False
        if cookie:
            session.headers.update({"Cookie": cookie})

        wait_msg("Fetching baseline...")
        try:
            resp = session.get(target, timeout=timeout)
            baseline = resp.text
            baseline_len = len(baseline)
            baseline_hash = hash(baseline[:1000])
        except Exception as e:
            error_then_exit(f"Could not reach target: {e}")

        # Extract forms/params
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(baseline, "html.parser")
        params = {}
        for form in soup.find_all("form"):
            for inp in form.find_all(["input", "textarea"]):
                name = inp.get("name")
                if name:
                    params[name] = inp.get("value", "")

        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(target)
        url_params = parse_qs(parsed.query)
        for k, v in url_params.items():
            params[k] = v[0] if v else ""

        if not params:
            warning("No parameters or forms detected. Using default param 'q'.")
            params = {"q": "test"}

        info(f"Found {len(params)} injection point(s). Testing payloads...")

        vulns_found: list[dict] = []
        payloads = VULN_PAYLOADS if VULN_PAYLOADS else {
            "SQL": ["'", "' OR '1'='1", "'; DROP TABLE--", "' UNION SELECT NULL--"],
            "XSS": ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"],
            "SSTI": ["{{7*7}}", "${7*7}", "<%= 7*7 %>"],
        }

        progress = Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), TextColumn("{task.percentage:>3.0f}%"))
        task = progress.add_task("Scanning...", total=len(params) * sum(len(p) for p in payloads.values()))
        with progress:
            for vuln_type, p_list in payloads.items():
                for pname, pval in params.items():
                    for payload in p_list:
                        try:
                            test_params = {pname: payload}
                            r = session.get(target, params=test_params, timeout=timeout)
                            if payload in r.text and payload not in baseline:
                                vulns_found.append({"type": vuln_type, "param": pname, "payload": payload, "status": r.status_code})
                                progress.console.log(f"[+] {vuln_type} detected in '{pname}'")
                        except Exception:
                            pass
                        progress.update(task, advance=1)

        if vulns_found:
            section_header("Vulnerabilities Found")
            table = make_table("Type", "Parameter", "Payload", "Status")
            for v in vulns_found:
                table.add_row(
                    Text(v["type"], style=Theme.error),
                    Text(v["param"], style=Theme.accent),
                    Text(v["payload"][:40], style=Theme.secondary),
                    str(v["status"]),
                )
            console.print(table)
        else:
            info("No vulnerabilities detected.")

        # Check for missing security headers
        sec_headers = [
            "Content-Security-Policy", "X-Frame-Options", "Strict-Transport-Security",
            "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
        ]
        missing = [h for h in sec_headers if h not in resp.headers]
        if missing:
            warning(f"Missing security headers: {', '.join(missing)}")

        pause()

    # ──────────────────────────────────────────────
    #  URL Discovery / Crawler
    # ──────────────────────────────────────────────
    def url_discovery(self):
        target = get_input("Target URL")
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        timeout_val = get_input("Timeout (s)", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        mode = get_input("Mode (onlypage/allwebsite)", "onlypage")

        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse

        session = requests.Session()
        session.verify = False
        urls_found: set[str] = set()
        to_visit = {target}
        visited: set[str] = set()

        progress = Progress(SpinnerColumn(), TextColumn("{task.description}"))
        task = progress.add_task(f"Crawling {target}...", total=None)

        with progress:
            while to_visit and len(visited) < 100:
                url = to_visit.pop()
                if url in visited:
                    continue
                visited.add(url)
                try:
                    r = session.get(url, timeout=timeout)
                    urls_found.add(url)
                    if mode == "allwebsite":
                        soup = BeautifulSoup(r.text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            full = urljoin(url, a["href"])
                            if urlparse(full).netloc == urlparse(target).netloc and full not in visited:
                                to_visit.add(full)
                    progress.update(task, description=f"[{Theme.primary}]Crawled {len(visited)} pages...")
                except Exception:
                    pass

        if urls_found:
            section_header(f"Discovered {len(urls_found)} URLs")
            table = make_table("#", "URL")
            for i, u in enumerate(sorted(urls_found)[:50], 1):
                table.add_row(str(i), Text(u, style=Theme.secondary))
            console.print(table)
            if len(urls_found) > 50:
                info(f"... and {len(urls_found) - 50} more")
        else:
            warning("No URLs discovered.")
        pause()

    # ──────────────────────────────────────────────
    #  IP Pinger
    # ──────────────────────────────────────────────
    def ip_pinger(self):
        target = get_input("Target IP")
        count = get_input("Ping count", "4")
        try:
            count = int(count)
        except ValueError:
            count = 4

        param = "-n" if sys.platform.startswith("win") else "-c"
        try:
            result = subprocess.run(
                ["ping", param, str(count), target],
                capture_output=True, text=True, timeout=30,
            )
            console.print(Text(result.stdout, style=Theme.secondary))
        except subprocess.TimeoutExpired:
            error("Ping timed out.")
        except FileNotFoundError:
            error("Ping command not found.")
        pause()

    # ──────────────────────────────────────────────
    #  Host Discovery
    # ──────────────────────────────────────────────
    def host_discovery(self):
        cidr = get_input("CIDR (e.g. 192.168.1.0/24)")
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            error_then_exit("Invalid CIDR.")

        timeout_val = get_input("Timeout (s)", "2")
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = 2

        progress = Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), TimeElapsedColumn())
        hosts_up: list[str] = []

        def _ping_host(ip: str) -> str | None:
            try:
                param = "-n" if sys.platform.startswith("win") else "-c"
                r = subprocess.run(["ping", param, "1", "-W", "1", ip], capture_output=True, text=True, timeout=timeout + 1)
                if r.returncode == 0:
                    return ip
            except Exception:
                pass
            return None

        total = network.num_addresses if network.num_addresses < 256 else 255
        task = progress.add_task(f"Scanning {cidr}...", total=total)
        with progress:
            with ThreadPoolExecutor(max_workers=50) as pool:
                futs = {pool.submit(_ping_host, str(ip)): str(ip) for ip in list(network.hosts())[:255]}
                for fut in as_completed(futs):
                    if fut.result():
                        hosts_up.append(fut.result())
                        success(f"Host up: {fut.result()}")
                    progress.update(task, advance=1)

        if hosts_up:
            section_header(f"Found {len(hosts_up)} live hosts")
            for h in sorted(hosts_up):
                console.print(f"  [{Theme.success}]+[/] {h}")
        else:
            warning("No live hosts found.")
        pause()
