import subprocess
import shutil
import sys
from pathlib import Path


def check_path() -> bool:
    python = shutil.which("python") or shutil.which("python3")
    pip = shutil.which("pip") or shutil.which("pip3")
    if not python:
        print("[x] Python not found in PATH.")
        return False
    if not pip:
        print("[x] Pip not found in PATH.")
        return False
    print("[!] Python and pip OK.")
    return True


def install_deps() -> None:
    req = Path(__file__).parent / "requirements.txt"
    print("[!] Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)
    except Exception:
        pass
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], check=True)
    print("[!] Dependencies installed.")


def main() -> None:
    print("=" * 60)
    print("  CHEAPY TOOL - Setup")
    print("  by psixakias.7 | discord.gg/cheapymarket")
    print("=" * 60)
    if check_path():
        install_deps()
        print("[!] Setup complete. Run: python main.py")


if __name__ == "__main__":
    main()
