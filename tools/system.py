from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import *

class AnonymizerModule:
    def __init__(self):
        self.is_admin = self._check_admin()
        if not self.is_admin:
            mark_admin_needed()

    def _check_admin(self) -> bool:
        if sys.platform.startswith("win"):
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            return os.geteuid() == 0

    def _run_cmd(self, cmd: str) -> str:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return r.stdout + r.stderr
        except Exception as e:
            return str(e)

    def _reg_delete(self, key: str) -> str:
        return self._run_cmd(f'reg delete "{key}" /f 2>nul')

    def _reg_add(self, key: str, value: str, data: str, typ: str = "REG_DWORD") -> str:
        return self._run_cmd(f'reg add "{key}" /v "{value}" /t {typ} /d "{data}" /f')

    # ─── Main Menu ──────────────────────────────
    def run(self):
        section_header("Windows 10/11 Anonymizer")
        console.print(Text("Hardens privacy, disables telemetry, removes bloatware", style=Theme.info))
        console.print()

        if not self.is_admin:
            warning("Run as Administrator for full functionality.")
            console.print()

        menu_items = [
            ("1", "Disable Telemetry & Data Collection"),
            ("2", "Disable Cortana & Bing Search"),
            ("3", "Disable OneDrive Completely"),
            ("4", "Remove Windows Bloatware Apps"),
            ("5", "Disable Wi-Fi Sense & Hotspots"),
            ("6", "Disable Advertising ID"),
            ("7", "Disable Location Tracking"),
            ("8", "Disable Background Apps"),
            ("9", "Disable P2P Updates"),
            ("10", "Disable Remote Access Services"),
            ("11", "Disable Defender Telemetry"),
            ("12", "Apply All Privacy Tweaks"),
            ("0", "Back to main menu"),
        ]

        table = make_table("Windows Anonymizer", ["#", "Tweak"])
        for num, label in menu_items:
            table.add_row(Text(num, style=Theme.primary), Text(label, style=Theme.secondary))
        console.print(table)

        choice = get_input("Select option")
        match choice:
            case "0":
                return
            case "1":
                self.disable_telemetry()
            case "2":
                self.disable_cortana()
            case "3":
                self.disable_onedrive()
            case "4":
                self.remove_bloatware()
            case "5":
                self.disable_wifi_sense()
            case "6":
                self.disable_advertising_id()
            case "7":
                self.disable_location()
            case "8":
                self.disable_background_apps()
            case "9":
                self.disable_p2p_updates()
            case "10":
                self.disable_remote_services()
            case "11":
                self.disable_defender_telemetry()
            case "12":
                self.apply_all()
            case _:
                error("Invalid choice.")
        pause()

    def disable_telemetry(self):
        info("Disabling telemetry...")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "AllowTelemetry", "0")
        self._reg_add("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection", "AllowTelemetry", "0")
        self._reg_add("HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection", "AllowTelemetry", "0")
        self._run_cmd("sc stop DiagTrack 2>nul")
        self._run_cmd("sc config DiagTrack start=disabled 2>nul")
        self._run_cmd("sc stop dmwappushservice 2>nul")
        self._run_cmd("sc config dmwappushservice start=disabled 2>nul")
        success("Telemetry disabled.")

    def disable_cortana(self):
        info("Disabling Cortana...")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "AllowCortana", "0")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "AllowSearchToUseLocation", "0")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "DisableWebSearch", "1")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "ConnectedSearchUseWeb", "0")
        self._reg_add("HKCU\\SOFTWARE\\Microsoft\\Personalization\\Settings", "AcceptedPrivacyPolicy", "0")
        self._reg_add("HKCU\\SOFTWARE\\Microsoft\\InputPersonalization", "RestrictImplicitTextCollection", "1")
        self._reg_add("HKCU\\SOFTWARE\\Microsoft\\InputPersonalization\\TrainedDataStore", "HarvestContacts", "0")
        success("Cortana & web search disabled.")

    def disable_onedrive(self):
        info("Disabling OneDrive...")
        self._run_cmd('taskkill /f /im OneDrive.exe 2>nul')
        self._run_cmd('%SystemRoot%\\SysWOW64\\OneDriveSetup.exe /uninstall 2>nul')
        self._run_cmd('%SystemRoot%\\System32\\OneDriveSetup.exe /uninstall 2>nul')
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive", "DisableFileSyncNGSC", "1")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive", "DisableLibrariesFileSync", "1")
        success("OneDrive disabled.")

    def remove_bloatware(self):
        info("Removing bloatware apps...")
        bloat = [
            "Microsoft.3DBuilder", "Microsoft.BingFinance", "Microsoft.BingNews",
            "Microsoft.BingSports", "Microsoft.BingWeather", "Microsoft.GetHelp",
            "Microsoft.Getstarted", "Microsoft.Messaging", "Microsoft.Microsoft3DViewer",
            "Microsoft.MicrosoftOfficeHub", "Microsoft.MicrosoftSolitaireCollection",
            "Microsoft.MixedReality.Portal", "Microsoft.Office.OneNote",
            "Microsoft.OneConnect", "Microsoft.People", "Microsoft.Print3D",
            "Microsoft.SkypeApp", "Microsoft.Wallet", "Microsoft.WindowsAlarms",
            "Microsoft.WindowsCamera", "Microsoft.WindowsCommunicationsApps",
            "Microsoft.WindowsFeedbackHub", "Microsoft.WindowsMaps",
            "Microsoft.WindowsSoundRecorder", "Microsoft.XboxApp",
            "Microsoft.XboxGameCallableUI", "Microsoft.XboxIdentityProvider",
            "Microsoft.XboxSpeechToTextOverlay", "Microsoft.XboxTCUI",
            "Microsoft.YourPhone", "Microsoft.ZuneMusic", "Microsoft.ZuneVideo",
            "Microsoft.Advertising.Xaml", "Microsoft.MSPaint",
            "Microsoft.Todos", "Microsoft.PowerAutomateDesktop",
            "Microsoft.Windows.DevHome", "Microsoft.Clipchamp",
            "Disney", "Spotify", "Netflix", "Twitter", "Facebook",
            "Instagram", "TikTok", "Amazon", "PrimeVideo", "Hulu",
        ]
        for app in bloat:
            result = self._run_cmd(f'winget uninstall "{app}" 2>nul')
            if "uninstalled" in result.lower():
                success(f"Removed: {app}")
        # Also use Get-AppxPackage
        self._run_cmd(
            'powershell -Command "Get-AppxPackage *3dbuilder* *bing* *officehub* '
            '*skype* *xbox* *zune* *maps* *camera* *alarms* *soundrecorder* '
        )
        # Remove all provisioned bloat
        self._run_cmd(
            'powershell -Command "Get-AppxPackage -AllUsers | '
            'Where-Object {$_.Name -match \'3DBuilder|Bing|Office|Skype|Xbox|Zune|Maps|Camera|Alarms|SoundRecorder|People|OneConnect\'} '
            '| Remove-AppxPackage -AllUsers 2>nul"'
        )
        success("Bloatware removal complete.")

    def disable_wifi_sense(self):
        info("Disabling Wi-Fi Sense & Hotspots...")
        self._reg_add("HKLM\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowWiFiHotSpotReporting", "value", "0")
        self._reg_add("HKLM\\SOFTWARE\\Microsoft\\WcmSvc\\wifinetworkmanager\\config", "AutoConnectAllowedOEM", "0")
        self._reg_add("HKLM\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowAutoConnectToWiFiSenseHotspots", "value", "0")
        success("Wi-Fi Sense disabled.")

    def disable_advertising_id(self):
        info("Disabling Advertising ID...")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AdvertisingInfo", "DisabledByGroupPolicy", "1")
        self._reg_add("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo", "Enabled", "0")
        success("Advertising ID disabled.")

    def disable_location(self):
        info("Disabling Location Tracking...")
        self._reg_add("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location", "Value", "Deny")
        self._reg_add("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Sensor\\Overrides\\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}", "SensorPermissionState", "0")
        self._reg_add("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeviceAccess\\Global\\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}", "Value", "Deny")
        # Disable sensor services
        self._run_cmd("sc stop SensrSvc 2>nul")
        self._run_cmd("sc config SensrSvc start=disabled 2>nul")
        success("Location tracking disabled.")

    def disable_background_apps(self):
        info("Disabling Background Apps...")
        self._reg_add("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications", "GlobalUserDisabled", "1")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AppPrivacy", "LetAppsRunInBackground", "2")
        success("Background apps disabled.")

    def disable_p2p_updates(self):
        info("Disabling P2P Update Delivery...")
        self._reg_add("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeliveryOptimization\\Config", "DODownloadMode", "0")
        self._run_cmd("sc stop DoSvc 2>nul")
        self._run_cmd("sc config DoSvc start=disabled 2>nul")
        success("P2P updates disabled.")

    def disable_remote_services(self):
        info("Disabling Remote Access Services...")
        services = ["RemoteRegistry", "TermService", "UmRdpService", "SessionEnv"]
        for s in services:
            self._run_cmd(f"sc stop {s} 2>nul")
            self._run_cmd(f"sc config {s} start=disabled 2>nul")
        self._reg_add("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server", "fDenyTSConnections", "1")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services", "fDenyTSConnections", "1")
        success("Remote services disabled.")

    def disable_defender_telemetry(self):
        info("Disabling Defender telemetry...")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender", "DisableAntiSpyware", "1")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Spynet", "SpynetReporting", "0")
        self._reg_add("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Spynet", "SubmitSamplesConsent", "2")
        success("Defender telemetry disabled.")

    def apply_all(self):
        info("Applying ALL privacy tweaks...")
        self.disable_telemetry()
        self.disable_cortana()
        self.disable_onedrive()
        self.remove_bloatware()
        self.disable_wifi_sense()
        self.disable_advertising_id()
        self.disable_location()
        self.disable_background_apps()
        self.disable_p2p_updates()
        self.disable_remote_services()
        self.disable_defender_telemetry()
        success("All privacy tweaks applied! Restart recommended.")

class CleanerModule:
    def __init__(self):
        self.cleaned_files = 0
        self.cleaned_bytes = 0

    def _clean_path(self, path: str, desc: str) -> None:
        p = Path(path)
        if not p.exists():
            return
        try:
            if p.is_file():
                size = p.stat().st_size
                p.unlink()
                self.cleaned_files += 1
                self.cleaned_bytes += size
                success(f"Deleted: {desc} ({size / 1024:.1f} KB)")
            elif p.is_dir():
                total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                shutil.rmtree(str(p))
                self.cleaned_files += 1
                self.cleaned_bytes += total
                success(f"Deleted: {desc} ({total / 1024:.1f} KB)")
        except PermissionError:
            warning(f"Access denied: {desc}")
        except Exception as e:
            warning(f"{desc}: {e}")

    def clean_temp_files(self):
        info("Cleaning temporary files...")
        temp_dirs = [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        ]
        for d in set(filter(None, temp_dirs)):
            self._clean_path(d, f"Temp folder: {d}")

        # Clean prefetch
        prefetch = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Prefetch")
        self._clean_path(prefetch, "Windows Prefetch")

        # Clean recent files
        recent = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent")
        self._clean_path(recent, "Recent files")

        success("Temp files cleaned.")

    def clean_browser_cache(self):
        info("Cleaning browser caches...")
        local_appdata = os.environ.get("LOCALAPPDATA", "")

        browsers = {
            "Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data", "Default", "Cache"),
            "Chrome (Code Cache)": os.path.join(local_appdata, "Google", "Chrome", "User Data", "Default", "Code Cache"),
            "Edge": os.path.join(local_appdata, "Microsoft", "Edge", "User Data", "Default", "Cache"),
            "Brave": os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Cache"),
            "Firefox": os.path.join(os.environ.get("APPDATA", ""), "Mozilla", "Firefox", "Profiles"),
            "Opera": os.path.join(local_appdata, "Opera Software", "Opera Stable", "Cache"),
            "Vivaldi": os.path.join(local_appdata, "Vivaldi", "User Data", "Default", "Cache"),
        }

        for name, path in browsers.items():
            if os.path.exists(path):
                self._clean_path(path, f"{name} cache")

        # Also clean Chrome/Edge session data
        for browser in ["Google", "Microsoft"]:
            sessions = Path(local_appdata) / browser / "Chrome" / "User Data" / "Default"
            for session_file in ["Session Storage", "Local Storage", "Service Worker", "File System"]:
                sp = sessions / session_file
                if sp.exists():
                    self._clean_path(str(sp), f"{browser} {session_file}")

        success("Browser caches cleaned.")

    def clean_logs(self):
        info("Cleaning system & app logs...")
        # Windows event logs
        self._run_cmd("wevtutil el 2>nul | findstr /r . >nul 2>nul")
        self._run_cmd('for /f "tokens=*" %a in (\'wevtutil el\') do wevtutil cl "%a" 2>nul')
        success("Windows event logs cleared.")

        # Clean pip cache
        pip_cache = Path.home() / ".cache" / "pip"
        if pip_cache.exists():
            self._clean_path(str(pip_cache), "Pip cache")

        # Clean npm cache
        npm_cache = Path.home() / ".npm" / "_cacache"
        if npm_cache.exists():
            self._clean_path(str(npm_cache), "NPM cache")

        # Clean yarn cache
        yarn_cache = Path.home() / "AppData" / "Local" / "Yarn" / "Cache"
        if yarn_cache.exists():
            self._clean_path(str(yarn_cache), "Yarn cache")

        # Clean pip logs
        pip_log = Path.home() / "pip" / "pip.log"
        if pip_log.exists():
            self._clean_path(str(pip_log), "Pip log")

        success("Logs cleaned.")

    def clean_recycle_bin(self):
        info("Emptying Recycle Bin...")
        if sys.platform.startswith("win"):
            self._run_cmd("powershell -Command \"Clear-RecycleBin -Force 2>nul\"")
            success("Recycle Bin emptied.")
        else:
            warning("Recycle Bin cleaning not available on this OS.")

    def clean_dns_cache(self):
        info("Flushing DNS cache...")
        if sys.platform.startswith("win"):
            self._run_cmd("ipconfig /flushdns >nul 2>nul")
        else:
            self._run_cmd("sudo systemd-resolve --flush-caches 2>/dev/null || killall -USR1 systemd-resolved 2>/dev/null || sudo dscacheutil -flushcache 2>/dev/null")
        success("DNS cache flushed.")

    def clean_prefetch(self):
        info("Cleaning Windows Prefetch...")
        prefetch = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Prefetch")
        self._clean_path(prefetch, "Windows Prefetch")
        success("Prefetch cleaned.")

    def clean_thumbnails(self):
        info("Cleaning thumbnail cache...")
        if sys.platform.startswith("win"):
            try:
                self._run_cmd("del /f /s /q /a %LocalAppData%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db >nul 2>nul")
                success("Thumbnail cache cleaned.")
            except Exception as e:
                warning(f"Thumbnails: {e}")

    def run_all(self):
        section_header("CCleaner - System Cleaner")
        console.print(Text("Cleans temp files, logs, caches, and junk data", style=Theme.info))
        console.print()

        menu_items = [
            ("1", "Clean Temp Files"),
            ("2", "Clean Browser Caches"),
            ("3", "Clean System & App Logs"),
            ("4", "Empty Recycle Bin"),
            ("5", "Flush DNS Cache"),
            ("6", "Clean Prefetch"),
            ("7", "Clean Thumbnails"),
            ("8", "CLEAN EVERYTHING (recommended)"),
            ("0", "Back"),
        ]

        table = make_table("System Cleaner", ["#", "Action"])
        for num, label in menu_items:
            table.add_row(Text(num, style=Theme.primary), Text(label, style=Theme.secondary))
        console.print(table)

        choice = get_input("Select option")
        self.cleaned_files = 0
        self.cleaned_bytes = 0

        match choice:
            case "0":
                return
            case "1":
                self.clean_temp_files()
            case "2":
                self.clean_browser_cache()
            case "3":
                self.clean_logs()
            case "4":
                self.clean_recycle_bin()
            case "5":
                self.clean_dns_cache()
            case "6":
                self.clean_prefetch()
            case "7":
                self.clean_thumbnails()
            case "8":
                self.clean_temp_files()
                self.clean_browser_cache()
                self.clean_logs()
                self.clean_recycle_bin()
                self.clean_dns_cache()
                self.clean_prefetch()
                self.clean_thumbnails()
            case _:
                error("Invalid choice.")

        if self.cleaned_bytes > 0:
            section_header("Cleanup Summary")
            info(f"Files deleted: {self.cleaned_files}")
            info(f"Space freed: {self.cleaned_bytes / 1024 / 1024:.2f} MB ({self.cleaned_bytes / 1024 / 1024 / 1024:.3f} GB)")
        pause()

    def _run_cmd(self, cmd: str) -> str:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return r.stdout + r.stderr
        except Exception as e:
            return str(e)
