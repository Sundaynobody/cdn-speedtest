import os, sys, platform, re, ctypes
import tkinter as tk
from . import constants
from .constants import _UI_FONT, _MONO_FONT


def get_config_dir():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "CDNSpeedTest")


def _cleanup_old_cache():
    cfg_dir = get_config_dir()
    if os.path.isdir(cfg_dir):
        for fname in os.listdir(cfg_dir):
            if fname.endswith(".json"):
                try:
                    os.remove(os.path.join(cfg_dir, fname))
                except Exception:
                    pass


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
    _cleanup_old_cache()
    return {
        "defaultIndex": constants.DEFAULT_CONFIG["defaultIndex"],
        "language": constants.DEFAULT_CONFIG["language"],
        "nodes": [dict(n) for n in constants.DEFAULT_CONFIG["nodes"]],
    }


def save_config(config):
    pass


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
