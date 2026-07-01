import os, sys, platform, json, re, ctypes
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from . import constants
from .i18n import t
from .constants import _UI_FONT, _MONO_FONT


def get_config_dir():
    p = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "CDNSpeedTest")
    os.makedirs(p, exist_ok=True)
    return p


constants._IP_CACHE_FILE = os.path.join(get_config_dir(), "ip_cache.json")
constants._load_ip_cache()


def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def get_dpi_factor(window):
    if platform.system() != "Windows":
        return 1.0
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(ctypes.wintypes.HWND(window.winfo_id()))
        if dpi > 0:
            return dpi / 96.0
    except Exception:
        pass
    return 1.0


def _get_monitor_dpi():
    if platform.system() == "Windows":
        try:
            hwnd = ctypes.windll.user32.GetDesktopWindow()
            monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
            dx = ctypes.c_uint(); dy = ctypes.c_uint()
            ctypes.windll.shcore.GetDpiForMonitor(monitor, 0, ctypes.byref(dx), ctypes.byref(dy))
            return dx.value
        except Exception:
            pass
    return 96


def set_window_icon(window):
    if platform.system() == "Windows":
        path = resource_path("icon.ico")
        if os.path.exists(path):
            try:
                window.iconbitmap(path)
                return
            except Exception:
                pass
    path = resource_path("icon.png")
    if os.path.exists(path):
        try:
            img = tk.PhotoImage(file=path)
            window.iconphoto(True, img)
        except Exception:
            pass


def load_config():
    path = os.path.join(get_config_dir(), constants.CONFIG_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                nodes = data.get("nodes", [])
                if isinstance(nodes, list) and len(nodes) > 0:
                    valid = [n for n in nodes if isinstance(n, dict) and "name" in n and "url" in n]
                    return {
                        "defaultIndex": data.get("defaultIndex", 0),
                        "language": data.get("language", "en"),
                        "nodes": valid or [dict(n) for n in constants.DEFAULT_CONFIG["nodes"]],
                    }
        except Exception:
            pass
    return {
        "defaultIndex": constants.DEFAULT_CONFIG["defaultIndex"],
        "language": constants.DEFAULT_CONFIG["language"],
        "nodes": [dict(n) for n in constants.DEFAULT_CONFIG["nodes"]],
    }


def save_config(config):
    path = os.path.join(get_config_dir(), constants.CONFIG_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror(t("save_failed"), t("save_failed_msg", e=str(e)))


def _format_speed(bps):
    if bps >= 1024*1024: return f"{bps/(1024*1024):.2f} MB/s"
    if bps >= 1024: return f"{bps/1024:.2f} KB/s"
    return f"{bps:.1f} B/s"


def _format_bytes(b):
    if b >= 1024*1024*1024: return f"{b/(1024*1024*1024):.2f} GB"
    if b >= 1024*1024: return f"{b/(1024*1024):.2f} MB"
    if b >= 1024: return f"{b/1024:.2f} KB"
    return f"{b} B"


def _fmt_time(sec):
    if sec is None or sec < 0: return "--"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s" if h else f"{m:02d}m{s:02d}s"


def _parse_speed(speed_str):
    if not speed_str:
        return 0
    s = str(speed_str)
    try:
        if "Gbps" in s:
            return float(s.split()[0]) * 1000
        elif "Mbps" in s:
            return float(s.split()[0])
    except Exception:
        pass
    return 0


def _clean_org(raw):
    s = re.sub(r'^AS\d+\s*', '', (raw or "")).strip()
    return s


def _normalize_isp(isp, asn):
    if asn and asn in constants._ISP_ASN_MAP:
        return constants._ISP_ASN_MAP[asn]
    return isp or ""
