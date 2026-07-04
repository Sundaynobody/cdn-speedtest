import ctypes, os, sys, platform, json, subprocess, time

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
        try:
            import certifi
            ctx.load_verify_locations(certifi.where())
        except ImportError:
            ctx.verify_mode = ssl.CERT_NONE
        ssl._create_default_https_context = lambda: ctx
    except Exception:
        pass

VERSION = "4.4.0"
CHUNK_SIZE = 1048576
UPDATE_INTERVAL = 1000
CONFIG_FILE = ""
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
_IP_CACHE_TTL = 300
_IP_CACHE_FILE = None

def _load_ip_cache():
    global _IP_CACHE
    if _IP_CACHE_FILE is None:
        return
    try:
        if os.path.isfile(_IP_CACHE_FILE):
            with open(_IP_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data.get("time", 0) < _IP_CACHE_TTL:
                _IP_CACHE.update(data)
    except Exception:
        pass

def _save_ip_cache():
    if _IP_CACHE_FILE is None:
        return
    try:
        os.makedirs(os.path.dirname(_IP_CACHE_FILE), exist_ok=True)
        tmp = _IP_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_IP_CACHE, f, ensure_ascii=False)
        os.replace(tmp, _IP_CACHE_FILE)
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
        {"name": "SpeedTest (7.0GB)", "url": "http://ota.justin-wg.com/Download/test.dat"},
        {"name": "China (Alibaba CDN 266MB)", "url": "https://wirelesscdn-download.xuexi.cn/publish/xuexi_android/latest/xuexi_android_10002068.apk"},
        {"name": "Hong Kong (DataPacket 100MB)", "url": "http://hkg.download.datapacket.com/100mb.bin"},
        {"name": "Japan (DataPacket 100MB)", "url": "http://tyo.download.datapacket.com/100mb.bin"},
        {"name": "Singapore (DataPacket 100MB)", "url": "http://sgp.download.datapacket.com/100mb.bin"},
        {"name": "US West (DataPacket 100MB)", "url": "http://lax.download.datapacket.com/100mb.bin"},
        {"name": "US East (DataPacket 100MB)", "url": "http://ash.download.datapacket.com/100mb.bin"},
        {"name": "France (DataPacket 100MB)", "url": "http://par.download.datapacket.com/100mb.bin"},
        {"name": "Singapore (Vultr 100MB)", "url": "https://sgp-ping.vultr.com/vultr.com.100MB.bin"},
        {"name": "US East (Vultr 100MB)", "url": "https://nj-us-ping.vultr.com/vultr.com.100MB.bin"},
        {"name": "Germany (Vultr 100MB)", "url": "https://fra-de-ping.vultr.com/vultr.com.100MB.bin"},
        {"name": "France (OVH 100MB)", "url": "https://proof.ovh.net/files/100Mb.dat"},
        {"name": "UK (ThinkBroadband 100MB)", "url": "http://ipv4.download.thinkbroadband.com/100MB.zip"},
        {"name": "Netherlands (IPVolume 100MB)", "url": "https://speedtest.ipvolume.net/100MB.bin"},
        {"name": "UK (Linode 100MB)", "url": "http://speedtest.london.linode.com/100MB-london.bin"},
        {"name": "Singapore (Linode 100MB)", "url": "http://speedtest.singapore.linode.com/100MB-singapore.bin"},
        {"name": "US East (Linode 100MB)", "url": "http://speedtest.newark.linode.com/100MB-newark.bin"},
        {"name": "Germany (Linode 100MB)", "url": "http://speedtest.frankfurt.linode.com/100MB-frankfurt.bin"},
        {"name": "Europe (Tele2 50MB)", "url": "http://speedtest.tele2.net/50MB.zip"},
        {"name": "Europe (Tele2 100MB)", "url": "http://speedtest.tele2.net/100MB.zip"},
    ],
}
