import os, json

VERSION = "1.0.0"
CHUNK_SIZE = 1048576
CONFIG_FILE = "cdn_nodes.json"

_IP_CACHE = {"ip": "", "loc": "", "asn": 0, "time": 0.0}
_IP_CACHE_TTL = 86400
_IP_CACHE_FILE = None

_ISP_ASN_MAP = {
    4134: "\u4e2d\u56fd\u7535\u4fe1", 4808: "\u4e2d\u56fd\u8054\u901a", 9808: "\u4e2d\u56fd\u79fb\u52a8",
    4837: "\u4e2d\u56fd\u8054\u901a", 9394: "\u4e2d\u56fd\u94c1\u901a", 58519: "\u4e2d\u56fd\u7535\u4fe1",
    4812: "\u4e2d\u56fd\u8054\u901a", 24445: "\u4e2d\u56fd\u79fb\u52a8", 56046: "\u4e2d\u56fd\u79fb\u52a8",
    17622: "\u4e2d\u56fd\u8054\u901a", 38283: "\u4e2d\u56fd\u7535\u4fe1",
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

def _get_config_dir():
    p = os.path.join(os.environ.get("HOME", os.path.expanduser("~")), ".cdn_speedtest")
    os.makedirs(p, exist_ok=True)
    return p

_IP_CACHE_FILE = os.path.join(_get_config_dir(), "ip_cache.json")

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

_load_ip_cache()
