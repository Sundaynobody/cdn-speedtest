import re, time, threading, concurrent.futures, requests
from . import constants
from .i18n import t

_IP_CACHE = constants._IP_CACHE
_IP_CACHE_TTL = constants._IP_CACHE_TTL


def _clean_org(raw):
    return re.sub(r'^AS\d+\s*', '', (raw or "")).strip()

def _normalize_isp(isp, asn):
    if asn and asn in constants._ISP_ASN_MAP:
        return constants._ISP_ASN_MAP[asn]
    return isp or ""


def _parse_ipinfo(data):
    ip = data.get("ip", "")
    if not ip:
        return None
    loc = data.get("city", "") or ""
    org = data.get("org", "").strip()
    asn = 0
    isp = _clean_org(org)
    if org:
        m = re.match(r'AS(\d+)', org)
        if m:
            asn = int(m.group(1))
    isp = _normalize_isp(isp, asn)
    if isp:
        loc += f" \u00B7 {isp}" if loc else isp
    if asn:
        loc += f" \u00B7 AS{asn}"
    return (ip, loc, asn)

def _parse_ipapi(data):
    ip = data.get("query", "")
    if not ip:
        return None
    parts = [p for p in [data.get("country"), data.get("regionName"),
                         data.get("city")] if p]
    loc = " \u2014 ".join(parts) if parts else ""
    isp = data.get("isp", "").strip()
    asn_str = data.get("as", "")
    asn = 0
    if asn_str:
        m = re.match(r'AS(\d+)', asn_str)
        if m:
            asn = int(m.group(1))
    isp = _normalize_isp(isp, asn)
    if isp:
        loc += f" \u00B7 {isp}"
    if asn:
        loc += f" \u00B7 AS{asn}"
    return (ip, loc, asn)


def get_ip_info(on_result, on_error=None):
    def task():
        now = time.time()
        if _IP_CACHE["ip"] and now - _IP_CACHE["time"] < _IP_CACHE_TTL:
            on_result(_IP_CACHE["ip"], _IP_CACHE["loc"])
            return
        services = [
            ("http://ip-api.com/json", 10, _parse_ipapi, 1),
            ("https://ipinfo.io/json", 8, _parse_ipinfo, 2),
        ]

        def fetch(url, timeout, parser):
            try:
                r = requests.get(url, timeout=timeout)
                return parser(r.json())
            except Exception:
                return None

        best = None
        top_prio = min(pri for *_, pri in services)
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=len(services))
        try:
            fut_prio = {ex.submit(fetch, u, timeout, p): pri
                        for u, timeout, p, pri in services}
            for f in concurrent.futures.as_completed(fut_prio):
                result = f.result()
                if result:
                    pri = fut_prio[f]
                    if best is None or pri < best[0]:
                        best = (pri, result[0], result[1], result[2])
                    # Highest-priority service answered; no need to wait
                    # for the slower fallbacks. (C4)
                    if best[0] == top_prio:
                        break
        finally:
            # Don't block on in-flight fallback requests; this runs in a
            # daemon thread so any leftover work is harmless. (C4)
            ex.shutdown(wait=False)

        if best:
            ip, loc, asn = best[1], best[2], best[3]
            _IP_CACHE["ip"] = ip
            _IP_CACHE["loc"] = loc
            _IP_CACHE["asn"] = asn
            _IP_CACHE["time"] = now
            constants._save_ip_cache()
            on_result(ip, loc)
        elif _IP_CACHE.get("ip"):
            on_result(_IP_CACHE["ip"], _IP_CACHE["loc"])
        else:
            (on_error or on_result)(t("failed"), "")

    threading.Thread(target=task, daemon=True).start()
