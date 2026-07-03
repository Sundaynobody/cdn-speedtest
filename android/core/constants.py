VERSION = "4.4.0"
CHUNK_SIZE = 1048576
CONFIG_FILE = ""

_IP_CACHE = {"ip": "", "loc": "", "asn": 0, "time": 0.0}
_IP_CACHE_TTL = 0
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

def _load_ip_cache():
    pass

def _save_ip_cache():
    pass
