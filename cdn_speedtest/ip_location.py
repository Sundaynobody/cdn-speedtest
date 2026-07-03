import time, json, os, re, threading, concurrent.futures, requests
from . import constants
from .i18n import t
from .utils import _clean_org, _normalize_isp, get_config_dir

_IP_CACHE = constants._IP_CACHE
_IP_CACHE_TTL = constants._IP_CACHE_TTL


class IpLocationMixin:

    @staticmethod
    def _parse_ipsb(data):
        ip = data.get("ip", "")
        if not ip:
            return None
        parts = [p for p in [data.get("country"), data.get("region"), data.get("city")] if p]
        loc = " \u2014 ".join(parts) if parts else ""
        isp = data.get("isp", "").strip()
        if not isp:
            org = data.get("organization", "").strip()
            if org:
                isp = _clean_org(org)
        asn = data.get("asn", 0)
        isp = _normalize_isp(isp, asn)
        if isp:
            loc += f" \u00B7 {isp}"
        if asn:
            loc += f" \u00B7 AS{asn}"
        return (ip, loc, asn)

    @staticmethod
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

    @staticmethod
    def _parse_ipapi(data):
        ip = data.get("query", "")
        if not ip:
            return None
        parts = [p for p in [data.get("country"), data.get("regionName"), data.get("city")] if p]
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

    def _show_ip_info(self, ip, loc, asn=0):
        self.ip_label.configure(text=ip)
        self.location_label.configure(text=loc)
        self._schedule_ip_refresh()

    def _schedule_ip_refresh(self):
        if self._ip_timer:
            self.root.after_cancel(self._ip_timer)
        self._ip_timer = self.root.after(300000, self._refresh_ip_info)

    def _refresh_ip_info(self):
        _IP_CACHE["time"] = 0
        self._fetch_ip_info()

    def _fetch_ip_info(self):
        def _task():
            now = time.time()
            if _IP_CACHE["ip"] and now - _IP_CACHE["time"] < _IP_CACHE_TTL:
                self.root.after(0, lambda: self._show_ip_info(_IP_CACHE["ip"], _IP_CACHE["loc"]))
                return
            services = [
                ("http://ip-api.com/json", 10, IpLocationMixin._parse_ipapi, 1),
                ("https://ipinfo.io/json", 8, IpLocationMixin._parse_ipinfo, 2),
            ]

            def _fetch(url, timeout, parser):
                try:
                    r = requests.get(url, timeout=timeout)
                    return parser(r.json())
                except Exception:
                    return None

            best = None
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                fut_prio = {ex.submit(_fetch, u, t, p): pri for u, t, p, pri in services}
                for f in concurrent.futures.as_completed(fut_prio):
                    result = f.result()
                    if result:
                        pri = fut_prio[f]
                        if best is None or pri < best[0]:
                            best = (pri, result[0], result[1], result[2])

            if best:
                ip, loc, asn = best[1], best[2], best[3]
                _IP_CACHE["ip"] = ip
                _IP_CACHE["loc"] = loc
                _IP_CACHE["asn"] = asn
                _IP_CACHE["time"] = now
                constants._save_ip_cache()
                self.root.after(0, lambda i=ip, l=loc, a=asn: self._show_ip_info(i, l, a))
            elif _IP_CACHE.get("ip"):
                self.root.after(0, lambda: self._show_ip_info(_IP_CACHE["ip"], _IP_CACHE["loc"]))
            else:
                self.root.after(0, lambda: self._show_ip_info(t("failed"), ""))

        threading.Thread(target=_task, daemon=True).start()
