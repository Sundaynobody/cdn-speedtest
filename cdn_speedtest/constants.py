import ctypes, os, sys, platform, json, subprocess

if platform.system() == "Windows":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# Windows 7 TLS 1.2 compatibility
if platform.system() == "Windows" and platform.release() == "7":
    try:
        import ssl
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ssl._create_default_https_context = lambda: ctx
    except Exception:
        pass

VERSION = "4.3.1"
CHUNK_SIZE = 1048576
UPDATE_INTERVAL = 1000
CONFIG_FILE = "cdn_nodes.json"
THEME = "cosmo"
_HIDE_CONSOLE = None
if platform.system() == "Windows":
    si = subprocess.STARTUPINFO()
    si.dwFlags = 0x01
    si.wShowWindow = 0
    _HIDE_CONSOLE = si

_UI_FONT = {"Windows": "Microsoft YaHei UI", "Darwin": "PingFang SC"}.get(platform.system(), "Noto Sans CJK")
_MONO_FONT = {"Windows": "Consolas", "Darwin": "Menlo"}.get(platform.system(), "Liberation Mono")

_IP_CACHE = {"ip": "", "loc": "", "asn": 0, "time": 0.0}
_IP_CACHE_TTL = 86400
_IP_CACHE_FILE = None

def _load_ip_cache():
    p = _IP_CACHE_FILE
    if p and os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("ip"):
                    _IP_CACHE.update(data)
        except Exception:
            pass

def _save_ip_cache():
    p = _IP_CACHE_FILE
    if p:
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(_IP_CACHE, f, ensure_ascii=False)
        except Exception:
            pass

_ISP_ASN_MAP = {
    4134: "中国电信", 4808: "中国联通", 9808: "中国移动",
    4837: "中国联通", 9394: "中国铁通", 58519: "中国电信",
    4812: "中国联通", 24445: "中国移动", 56046: "中国移动",
    17622: "中国联通", 38283: "中国电信",
    7922: "Comcast", 7018: "AT&T", 3320: "Deutsche Telekom",
    1239: "Sprint", 2914: "NTT", 3491: "BT",
    7132: "AT&T", 22773: "Cox", 20115: "Charter",
    5089: "Virgin Media", 6830: "Liberty Global",
    174: "Cogent", 6453: "Tata", 5511: "Orange",
    3215: "Orange", 15557: "SFR",
    6849: "Ukraine", 8402: "VimpelCom",
}

DEFAULT_CONFIG = {
    "defaultIndex": 0,
    "language": "en",
    "nodes": [
        {"name": "Europe (Tele2 50MB)", "url": "http://speedtest.tele2.net/50MB.zip"},
        {"name": "Europe (Tele2 100MB)", "url": "http://speedtest.tele2.net/100MB.zip"},
        {"name": "Asia (Linode SG 100MB)", "url": "http://speedtest.singapore.linode.com/100MB-singapore.bin"},
        {"name": "US East (Linode NJ 100MB)", "url": "http://speedtest.newark.linode.com/100MB-newark.bin"},
        {"name": "Europe (Linode DE 100MB)", "url": "http://speedtest.frankfurt.linode.com/100MB-frankfurt.bin"},
    ],
}
