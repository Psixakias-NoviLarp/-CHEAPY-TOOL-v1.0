from __future__ import annotations

import sys
import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import *


class IpWebExtendedModule:
    def run(self):
        section_header("Extended IP & Web Tools")
        console.print()
        menu_items = [
            ("1", "IP Geolocation (Detailed)"),
            ("2", "Subdomain Scanner"),
            ("3", "Directory Discovery"),
            ("4", "Reverse IP Lookup"),
            ("5", "HTTP Security Headers Scan"),
            ("6", "SSL/TLS Certificate Info"),
            ("7", "Website Technology Detector"),
            ("8", "Ping Test"),
            ("9", "Traceroute"),
            ("10", "Port Scan (Quick 1-1024)"),
            ("11", "DNS Record Lookup"),
            ("12", "Whois Lookup"),
            ("13", "HTTP Request Inspector"),
            ("14", "CDN/Proxy Detection"),
            ("15", "Server Info Grabber"),
            ("0", "Back"),
        ]
        table = make_table("IP & Web Extended", ["#", "Tool"])
        for num, label in menu_items:
            table.add_row(Text(num, style=Theme.primary), Text(label, style=Theme.secondary))
        console.print(table)
        choice = get_input("Select tool")
        match choice:
            case "0": return
            case "1": self.geolocation()
            case "2": self.subdomain_scan()
            case "3": self.dir_discovery()
            case "4": self.reverse_ip()
            case "5": self.security_headers()
            case "6": self.ssl_info()
            case "7": self.tech_detect()
            case "8": self.ping_test()
            case "9": self.traceroute()
            case "10": self.quick_port_scan()
            case "11": self.dns_lookup()
            case "12": self.whois_lookup()
            case "13": self.http_inspect()
            case "14": self.cdn_detect()
            case "15": self.server_info()
            case _: error("Invalid.")
        pause()

    def _req(self, url, timeout=10):
        try:
            return requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
        except Exception:
            return None

    def geolocation(self):
        ip = get_input("IP address")
        r = self._req(f"https://ipapi.co/{ip}/json/")
        if r and r.status_code == 200:
            d = r.json()
            t = make_table("Geolocation", ["Field", "Value"])
            for k, v in d.items():
                if v is not None and v != "":
                    t.add_row(Text(k.replace("_", " ").title(), style=Theme.accent), Text(str(v)[:60], style=Theme.secondary))
            console.print(t)
        else:
            # Fallback to ip-api
            r2 = self._req(f"http://ip-api.com/json/{ip}")
            if r2 and r2.status_code == 200:
                d = r2.json()
                if d.get("status") == "success":
                    t = make_table("Geolocation (ip-api)", ["Field", "Value"])
                    fields = [("IP", "query"), ("Country", "country"), ("Region", "regionName"), ("City", "city"), ("ZIP", "zip"), ("Lat", "lat"), ("Lon", "lon"), ("ISP", "isp"), ("ORG", "org"), ("AS", "as"), ("Timezone", "timezone"), ("Mobile", "mobile"), ("Proxy", "proxy"), ("Hosting", "hosting")]
                    for label, key in fields:
                        val = d.get(key)
                        if val is not None and val != "":
                            t.add_row(Text(label, style=Theme.accent), Text(str(val), style=Theme.secondary))
                    console.print(t)
                else:
                    error(f"API: {d.get('message', 'error')}")
            else:
                error("Could not fetch geolocation.")
        pause()

    def subdomain_scan(self):
        domain = get_input("Domain (e.g. example.com)")
        wordlist_str = get_input("Wordlist (comma-separated, or 'common' for built-in)", "common")

        common = ["www", "mail", "admin", "blog", "api", "dev", "test", "staging", "vpn", "remote", "webmail", "support", "help", "forum", "docs", "wiki", "cdn", "static", "assets", "img", "images", "video", "media", "download", "ftp", "smtp", "pop", "imap", "owa", "exchange", "confluence", "jira", "gitlab", "jenkins", "kibana", "grafana", "prometheus", "dashboard", "monitor", "status", "portal", "app", "m", "mobile", "shop", "store", "checkout", "login", "register", "signup", "auth", "oauth", "sso", "saml", "ldap", "radius", "ns1", "ns2", "ns3", "mx1", "mx2", "mx3", "sip", "voip", "phone", "chat", "meet", "team", "zoom", "webex", "teams", "slack", "discord", "reddit", "facebook", "twitter", "instagram", "youtube", "linkedin", "pinterest", "tumblr", "snapchat", "whatsapp", "telegram", "signal", "wechat", "alibaba", "amazon", "google", "microsoft", "apple", "netflix", "spotify", "twitch", "steam", "epic", "origin", "ubisoft", "ea", "activision", "blizzard", "riot", "valve", "bethesda", "square", "capcom", "sega", "nintendo", "sony", "microsoft", "oracle", "ibm", "hp", "dell", "cisco", "vmware", "redhat", "ubuntu", "debian", "centos", "fedora", "arch", "gentoo", "slackware", "opensuse", "suse", "mandriva", "mint", "kali", "parrot", "blackarch", "backbox", "fedora", "openshift", "kubernetes", "docker", "k8s", "rancher", "minikube", "podman", "containerd", "crio", "gcr", "ecr", "acr", "dockerhub", "quay", "harbor", "nexus", "artifactory", "jfrog", "sonatype", "npm", "pypi", "rubygems", "crates", "packagist", "nuget", "maven", "gradle", "sbt", "leiningen", "cocoapods", "carthage", "spm", "bower", "yarn", "pnpm", "bun", "deno", "node", "python", "ruby", "php", "perl", "lua", "go", "rust", "java", "scala", "kotlin", "groovy", "clojure", "erlang", "elixir", "haskell", "ocaml", "fsharp", "csharp", "dotnet", "asp", "jsp", "cfm", "shtml", "dhtml", "xhtml", "html", "htm", "php", "asp", "aspx", "jsp", "cfm", "shtml", "dhtml", "swf", "flv", "mp3", "mp4", "avi", "mov", "wmv", "flv", "swf", "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "csv", "tsv", "xml", "json", "yaml", "yml", "toml", "ini", "cfg", "conf", "config", "env", "htaccess", "htpasswd"]

        wordlist = common if wordlist_str == "common" else [w.strip() for w in wordlist_str.split(",") if w.strip()]
        found = []

        import dns.resolver
        progress_table = make_table("Subdomains", ["Subdomain", "IP", "Status"])
        with ThreadPoolExecutor(max_workers=50) as pool:
            def _check(sub):
                target = f"{sub}.{domain}"
                try:
                    ips = dns.resolver.resolve(target, "A", lifetime=5)
                    ip = str(ips[0])
                    # Verify HTTP
                    try:
                        r = requests.get(f"http://{target}", timeout=5, verify=False)
                        return (target, ip, r.status_code)
                    except Exception:
                        return (target, ip, "?")
                except Exception:
                    return None
            futs = {pool.submit(_check, sub): sub for sub in wordlist}
            for fut in as_completed(futs):
                result = fut.result()
                if result:
                    found.append(result)
                    progress_table.add_row(Text(result[0], style=Theme.success), Text(result[1], style=Theme.secondary), Text(str(result[2]), style=Theme.accent))

        if found:
            section_header(f"Found {len(found)} subdomains")
            console.print(progress_table)
        else:
            warning("No subdomains found.")
        info(f"Scanned {len(wordlist)} names in wordlist.")
        pause()

    def dir_discovery(self):
        target = get_input("Target URL (e.g. https://example.com)")
        if not target.startswith("http"):
            target = f"https://{target}"

        wordlist_str = get_input("Wordlist (comma-separated, or 'common')", "common")
        common = ["admin", "login", "wp-admin", "admin.php", "administrator", "backup", "config", "db", "database", "sql", "dump", "test", "dev", "api", "v1", "v2", "graphql", "rest", "soap", "xmlrpc", ".env", ".git", ".svn", "robots.txt", "sitemap.xml", "crossdomain.xml", "phpinfo.php", "info.php", "status", "health", "healthcheck", "actuator", "swagger", "docs", "api-docs", "openapi", "swagger.json", "swagger.yaml", "swagger-ui", "api/swagger", "api/docs", "api/v1/docs", "api/v2/docs", "graphql", "graphiql", "playground", "altair", "voyager", "adminer", "phpmyadmin", "pma", "mysql", "phpPgAdmin", "pgadmin", "admin/", "backup/", "uploads/", "assets/", "static/", "public/", "private/", "temp/", "tmp/", "logs/", "error_log", "debug", "install", "setup", "configure", "config.php", "config.json", "config.yaml", "config.yml", "config.toml", "config.ini", "settings", "settings.php", "database.php", "db.php", "connection.php", "conn.php"]
        wordlist = common if wordlist_str == "common" else [w.strip() for w in wordlist_str.split(",") if w.strip()]
        found = []

        target = target.rstrip("/")
        with ThreadPoolExecutor(max_workers=20) as pool:
            def _check(path):
                url = f"{target}/{path}"
                try:
                    r = requests.get(url, timeout=5, verify=False)
                    if r.status_code in (200, 201, 204, 301, 302, 307, 401, 403):
                        return (path, r.status_code, len(r.text))
                except Exception:
                    pass
                return None
            futs = {pool.submit(_check, p): p for p in wordlist}
            for fut in as_completed(futs):
                result = fut.result()
                if result:
                    found.append(result)

        if found:
            section_header(f"Found {len(found)} paths")
            t = make_table("Directory Discovery", ["Path", "Status", "Size"])
            for path, status, size in sorted(found, key=lambda x: x[1]):
                status_color = Theme.success if status in (200, 201, 204) else Theme.warning if status in (301, 302) else Theme.error if status in (401, 403) else Theme.secondary
                t.add_row(Text(f"/{path}", style=Theme.secondary), Text(str(status), style=status_color), Text(f"{size:,}B", style=Theme.muted))
            console.print(t)
        else:
            warning("No paths discovered.")
        info(f"Scanned {len(wordlist)} paths.")
        pause()

    def reverse_ip(self):
        ip = get_input("IP address")
        r = self._req(f"https://api.hackertarget.com/reverseiplookup/?q={ip}")
        if r and r.status_code == 200:
            section_header("Reverse IP (domains on this server)")
            for line in r.text.strip().split("\n")[:50]:
                console.print(Text(f"  {line}", style=Theme.secondary))
        else:
            r2 = self._req(f"https://yougetsignal.com/tools/web-sites-on-web-server/")
            if r2 and r2.status_code == 200:
                info("Check: https://yougetsignal.com/tools/web-sites-on-web-server/")
            else:
                warning("Could not fetch reverse IP data.")
        pause()

    def security_headers(self):
        target = get_input("Target URL")
        if not target.startswith("http"):
            target = f"https://{target}"
        r = self._req(target)
        if not r:
            error("Could not reach target.")
            return
        section_header("Security Headers")
        h = r.headers
        checks = [
            ("Content-Security-Policy", "CSP", True),
            ("X-Frame-Options", "Clickjacking Protection", True),
            ("Strict-Transport-Security", "HSTS", True),
            ("X-Content-Type-Options", "MIME Sniffing Protection", True),
            ("Referrer-Policy", "Referrer Policy", True),
            ("Permissions-Policy", "Permissions Policy", True),
            ("X-XSS-Protection", "XSS Filter", False),
            ("Access-Control-Allow-Origin", "CORS", None),
            ("Set-Cookie", "Cookies", None),
        ]
        t = make_table("Security Headers", ["Header", "Status", "Value"])
        for header_name, desc, required in checks:
            val = h.get(header_name, "")
            if val:
                status = Text(f"Present ({desc})", style=Theme.success)
                t.add_row(Text(header_name, style=Theme.accent), status, Text(str(val)[:60], style=Theme.secondary))
            elif required:
                t.add_row(Text(header_name, style=Theme.accent), Text(f"MISSING ({desc})", style=Theme.error), Text("", style=Theme.secondary))
            else:
                t.add_row(Text(header_name, style=Theme.accent), Text(f"Not set", style=Theme.muted), Text("", style=Theme.secondary))
        console.print(t)
        pause()

    def ssl_info(self):
        import ssl as _ssl
        import socket as _socket
        from datetime import datetime as _dt
        host = get_input("Host (e.g. example.com)")
        try:
            ctx = _ssl.create_default_context()
            with _socket.create_connection((host, 443), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    t = make_table("SSL/TLS Certificate", ["Field", "Value"])
                    t.add_row(Text("Subject", style=Theme.accent), Text(str(cert.get("subject", [])), style=Theme.secondary))
                    t.add_row(Text("Issuer", style=Theme.accent), Text(str(cert.get("issuer", [])), style=Theme.secondary))
                    t.add_row(Text("Version", style=Theme.accent), Text(f"TLS {ssock.version()}", style=Theme.secondary))
                    t.add_row(Text("Cipher", style=Theme.accent), Text(ssock.cipher()[0], style=Theme.secondary))
                    not_before = _dt.strptime(cert.get("notBefore", ""), "%b %d %H:%M:%S %Y %Z")
                    not_after = _dt.strptime(cert.get("notAfter", ""), "%b %d %H:%M:%S %Y %Z")
                    t.add_row(Text("Valid From", style=Theme.accent), Text(not_before.strftime("%Y-%m-%d"), style=Theme.secondary))
                    t.add_row(Text("Valid Until", style=Theme.accent), Text(not_after.strftime("%Y-%m-%d"), style=Theme.secondary))
                    t.add_row(Text("Days Remaining", style=Theme.accent), Text(str((not_after - _dt.utcnow()).days), style=Theme.success if (not_after - _dt.utcnow()).days > 30 else Theme.error))
                    console.print(t)
        except Exception as e:
            error(f"SSL error: {e}")
        pause()

    def tech_detect(self):
        target = get_input("Target URL")
        if not target.startswith("http"):
            target = f"https://{target}"
        r = self._req(target)
        if not r:
            error("Could not reach target.")
            return
        section_header("Technology Detection")
        h = r.headers
        html = r.text.lower()
        t = make_table("Technologies", ["Technology", "Evidence"])
        # Server
        server = h.get("Server", "")
        if server:
            t.add_row(Text("Server", style=Theme.accent), Text(server, style=Theme.secondary))
        # X-Powered-By
        powered = h.get("X-Powered-By", "")
        if powered:
            t.add_row(Text("Powered By", style=Theme.accent), Text(powered, style=Theme.secondary))
        # CMS detection
        if "wp-content" in html or "wp-includes" in html or "wordpress" in html:
            t.add_row(Text("CMS", style=Theme.accent), Text("WordPress", style=Theme.secondary))
        elif "joomla" in html:
            t.add_row(Text("CMS", style=Theme.accent), Text("Joomla", style=Theme.secondary))
        elif "drupal" in html:
            t.add_row(Text("CMS", style=Theme.accent), Text("Drupal", style=Theme.secondary))
        # JS frameworks
        if "react" in html or "reactjs" in html or "react.js" in html:
            t.add_row(Text("JS Framework", style=Theme.accent), Text("React", style=Theme.secondary))
        if "angular" in html:
            t.add_row(Text("JS Framework", style=Theme.accent), Text("Angular", style=Theme.secondary))
        if "vue" in html or "vuejs" in html or "vue.js" in html:
            t.add_row(Text("JS Framework", style=Theme.accent), Text("Vue.js", style=Theme.secondary))
        # jQuery
        if "jquery" in html:
            t.add_row(Text("Library", style=Theme.accent), Text("jQuery", style=Theme.secondary))
        # Cloudflare
        if "cloudflare" in html or h.get("CF-RAY"):
            t.add_row(Text("CDN", style=Theme.accent), Text("Cloudflare", style=Theme.secondary))
        # Google Analytics
        if "google-analytics" in html or "gtag(" in html or "ga(" in html:
            t.add_row(Text("Analytics", style=Theme.accent), Text("Google Analytics", style=Theme.secondary))
        # Nginx
        if "nginx" in server.lower():
            t.add_row(Text("Web Server", style=Theme.accent), Text("Nginx", style=Theme.secondary))
        elif "apache" in server.lower():
            t.add_row(Text("Web Server", style=Theme.accent), Text("Apache", style=Theme.secondary))
        elif "cloudflare" in server.lower():
            t.add_row(Text("Web Server", style=Theme.accent), Text("Cloudflare", style=Theme.secondary))
        if not t.row_count:
            t.add_row(Text("Detection", style=Theme.accent), Text("No specific technologies detected", style=Theme.muted))
        console.print(t)
        pause()

    def ping_test(self):
        import subprocess as _sp
        host = get_input("Host or IP")
        param = "-n" if sys.platform.startswith("win") else "-c"
        try:
            r = _sp.run(["ping", param, "4", host], capture_output=True, text=True, timeout=30)
            console.print(Text(r.stdout, style=Theme.secondary))
            if r.stderr:
                console.print(Text(r.stderr, style=Theme.error))
        except Exception as e:
            error(f"Ping error: {e}")
        pause()

    def traceroute(self):
        import subprocess as _sp
        host = get_input("Host or IP")
        try:
            if sys.platform.startswith("win"):
                r = _sp.run(["tracert", "-h", "15", host], capture_output=True, text=True, timeout=60)
            else:
                r = _sp.run(["traceroute", "-m", "15", host], capture_output=True, text=True, timeout=60)
            console.print(Text(r.stdout, style=Theme.secondary))
        except FileNotFoundError:
            error("Traceroute command not found.")
        except Exception as e:
            error(f"Error: {e}")
        pause()

    def quick_port_scan(self):
        host = get_input("Host or IP")
        try:
            ip = socket.gethostbyname(host)
        except Exception:
            ip = host
        info(f"Resolved: {ip}")
        info("Scanning ports 1-1024...")
        open_ports = []
        with ThreadPoolExecutor(max_workers=200) as pool:
            def _scan(port):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1)
                    r = s.connect_ex((ip, port))
                    s.close()
                    return port if r == 0 else None
                except Exception:
                    return None
            futs = {pool.submit(_scan, p): p for p in range(1, 1025)}
            for fut in as_completed(futs):
                result = fut.result()
                if result:
                    open_ports.append(result)
        if open_ports:
            section_header(f"Open Ports ({len(open_ports)})")
            t = make_table("Port", "Service")
            for p in sorted(open_ports):
                svc = socket.getservbyport(p) if p <= 49151 else "ephemeral"
                t.add_row(Text(str(p), style=Theme.primary), Text(svc, style=Theme.secondary))
            console.print(t)
        else:
            warning("No open ports found (1-1024).")
        pause()

    def dns_lookup(self):
        import dns.resolver as _dr
        domain = get_input("Domain")
        for qtype in ("A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "SRV"):
            try:
                answers = _dr.resolve(domain, qtype, lifetime=5)
                for a in answers:
                    info(f"[{qtype}] {a}")
            except Exception:
                pass
        pause()

    def whois_lookup(self):
        domain = get_input("Domain or IP")
        try:
            import whois as _whois
            w = _whois.whois(domain)
            t = make_table("WHOIS", ["Field", "Value"])
            for k, v in w.items():
                if v:
                    if isinstance(v, list):
                        v = ", ".join(str(x) for x in v[:5])
                    t.add_row(Text(str(k), style=Theme.accent), Text(str(v)[:100], style=Theme.secondary))
            console.print(t)
        except ImportError:
            warning("python-whois not installed.")
            info(f"Check: https://who.is/{domain}")
        except Exception as e:
            error(f"WHOIS error: {e}")
        pause()

    def http_inspect(self):
        url = get_input("URL to inspect")
        if not url.startswith("http"):
            url = f"https://{url}"
        r = self._req(url)
        if r:
            section_header("HTTP Request Inspector")
            t = make_table("Response Info", ["Property", "Value"])
            t.add_row(Text("URL", style=Theme.accent), Text(r.url, style=Theme.secondary))
            t.add_row(Text("Status", style=Theme.accent), Text(str(r.status_code), style=Theme.success if r.status_code < 400 else Theme.error))
            t.add_row(Text("Elapsed", style=Theme.accent), Text(f"{r.elapsed.total_seconds():.3f}s", style=Theme.secondary))
            t.add_row(Text("Content-Type", style=Theme.accent), Text(r.headers.get("Content-Type", "?"), style=Theme.secondary))
            t.add_row(Text("Content-Length", style=Theme.accent), Text(f"{len(r.content):,} bytes", style=Theme.secondary))
            t.add_row(Text("Encoding", style=Theme.accent), Text(r.encoding or "?", style=Theme.secondary))
            t.add_row(Text("Cookies", style=Theme.accent), Text(str(len(r.cookies)), style=Theme.secondary))
            t.add_row(Text("Redirects", style=Theme.accent), Text(str(len(r.history)), style=Theme.secondary))
            console.print(t)
            if r.history:
                section_header("Redirect Chain")
                for i, resp in enumerate(r.history):
                    info(f"{'  ' * i}{resp.status_code} -> {resp.url}")
            section_header("Response Headers")
            ht = make_table("Header", "Value")
            for k, v in r.headers.items():
                ht.add_row(Text(k, style=Theme.accent), Text(v[:100], style=Theme.secondary))
            console.print(ht)
        else:
            error("Could not reach URL.")
        pause()

    def cdn_detect(self):
        target = get_input("Target URL")
        if not target.startswith("http"):
            target = f"https://{target}"
        r = self._req(target)
        if r:
            h = r.headers
            t = make_table("CDN/Proxy Detection", ["Indicator", "Value"])
            cf = h.get("CF-RAY") or h.get("cf-ray")
            if cf:
                t.add_row(Text("Cloudflare", style=Theme.accent), Text(f"CF-RAY: {cf}", style=Theme.secondary))
            if h.get("Server") and "cloudflare" in h["Server"].lower():
                t.add_row(Text("Cloudflare Server", style=Theme.accent), Text(h["Server"], style=Theme.secondary))
            if h.get("X-Served-By"):
                t.add_row(Text("X-Served-By", style=Theme.accent), Text(h["X-Served-By"], style=Theme.secondary))
            if h.get("X-Cache"):
                t.add_row(Text("X-Cache", style=Theme.accent), Text(h["X-Cache"], style=Theme.secondary))
            if h.get("Via"):
                t.add_row(Text("Via", style=Theme.accent), Text(h["Via"], style=Theme.secondary))
            if h.get("Akamai-Request-ID") or h.get("X-Akamai-"):
                t.add_row(Text("Akamai", style=Theme.accent), Text("Akamai CDN detected", style=Theme.secondary))
            if h.get("Fastly-Debug"):
                t.add_row(Text("Fastly", style=Theme.accent), Text("Fastly CDN detected", style=Theme.secondary))
            if h.get("X-GUploader-UploadID") or h.get("X-Google-"):
                t.add_row(Text("Google Cloud", style=Theme.accent), Text("Google infrastructure", style=Theme.secondary))
            if h.get("X-Amz-") or h.get("x-amz-"):
                t.add_row(Text("AWS", style=Theme.accent), Text("AWS infrastructure", style=Theme.secondary))
            if not t.row_count:
                t.add_row(Text("No CDN/Proxy", style=Theme.accent), Text("Direct connection likely", style=Theme.muted))
            console.print(t)
        pause()

    def server_info(self):
        target = get_input("Target URL")
        if not target.startswith("http"):
            target = f"https://{target}"
        r = self._req(target)
        if r:
            section_header("Server Information")
            h = r.headers
            t = make_table("Server Info", ["Header", "Value"])
            interesting = ["Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version", "X-Generator", "X-Drupal-Cache", "X-Drupal-Dynamic-Cache", "X-Varnish", "Age", "Via", "X-Cache", "X-Cache-Hits", "X-Backend", "X-Proxy-Cache", "CF-RAY", "CF-Cache-Status", "CF-Worker", "Server-Timing", "X-Served-By", "X-Request-Id", "X-Trace-Id", "X-Amzn-Trace-Id", "X-Runtime", "X-Version"]
            for header_name in interesting:
                val = h.get(header_name)
                if val:
                    t.add_row(Text(header_name, style=Theme.accent), Text(str(val)[:80], style=Theme.secondary))
            console.print(t)
        else:
            error("Could not reach target.")
        pause()
