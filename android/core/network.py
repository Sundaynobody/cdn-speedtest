import subprocess, platform, os, re

try:
    import android
    _ON_ANDROID = True
except ImportError:
    _ON_ANDROID = False


class NetworkMixin:

    def get_network_info(self):
        data = {"type": "unknown", "ssid": "", "rate": 0, "band": "", "signal": 0}
        try:
            sys = platform.system()
            if _ON_ANDROID or sys == "Linux":
                data = self._linux_get_net() or data
            elif sys == "Darwin":
                data = self._mac_get_wifi() or self._mac_get_eth() or data
        except Exception:
            pass
        return data

    @staticmethod
    def _parse_speed(speed_str):
        if not speed_str:
            return 0
        try:
            s = str(speed_str)
            if "Gbps" in s:
                return float(s.split()[0]) * 1000
            elif "Mbps" in s:
                return float(s.split()[0])
        except Exception:
            pass
        return 0

    def _linux_get_net(self):
        try:
            import glob
            for dev in glob.glob("/sys/class/net/*"):
                name = dev.split("/")[-1]
                try:
                    op = open(f"{dev}/operstate").read().strip()
                except Exception:
                    continue
                if op != "up":
                    continue
                if os.path.isdir(f"{dev}/wireless"):
                    r = subprocess.run(["iw", "dev", name, "link"],
                                       capture_output=True, text=True, timeout=5)
                    if r.returncode != 0:
                        continue
                    d = {"type": "wifi", "ssid": "", "rate": 0,
                         "band": "", "signal": 0}
                    for line in r.stdout.splitlines():
                        s = line.strip()
                        if s.startswith("SSID:"):
                            d["ssid"] = s.split(":", 1)[1].strip()
                        elif "freq:" in s:
                            try:
                                freq = int(s.split(":")[1].strip().split()[0])
                                d["band"] = "6 GHz" if freq > 6000 else (
                                    "5 GHz" if freq > 2500 else "2.4 GHz")
                            except Exception:
                                pass
                        elif "tx bitrate:" in s:
                            m = re.search(r'([\d.]+)\s*MBit/s', s)
                            if m:
                                d["rate"] = float(m.group(1))
                    if d["ssid"]:
                        return d
                else:
                    try:
                        speed = int(open(f"{dev}/speed").read().strip())
                        if speed > 0:
                            return {"type": "ethernet", "ssid": "",
                                    "rate": speed, "band": "", "signal": 0}
                    except Exception:
                        pass
            return None
        except Exception:
            return None

    def _mac_get_wifi(self):
        try:
            airport = ("/System/Library/PrivateFrameworks/Apple80211.framework/"
                       "Versions/Current/Resources/airport")
            if not os.path.exists(airport):
                airport = "/usr/sbin/airport"
                if not os.path.exists(airport):
                    return None
            r = subprocess.run([airport, "-I"], capture_output=True,
                               text=True, timeout=5)
            if r.returncode != 0:
                return None
            d = {"type": "wifi", "ssid": "", "rate": 0,
                 "band": "", "signal": 0}
            for line in r.stdout.splitlines():
                s = line.strip()
                if s.startswith("SSID"):
                    d["ssid"] = s.split(":", 1)[1].strip()
                elif "lastTxRate" in s:
                    try:
                        d["rate"] = float(s.split(":", 1)[1].strip())
                    except Exception:
                        pass
                elif s.startswith("channel"):
                    try:
                        ch_str = s.split(":", 1)[1].strip()
                        ch = int(ch_str.split(",")[0].strip())
                        d["band"] = "6 GHz" if ch > 165 else (
                            "5 GHz" if ch > 13 else "2.4 GHz")
                    except Exception:
                        pass
            return d if d["ssid"] else None
        except Exception:
            return None

    def _mac_get_eth(self):
        try:
            r = subprocess.run(["ifconfig", "-l"], capture_output=True,
                               text=True, timeout=3)
            ifaces = r.stdout.strip().split()
            for iface in ifaces:
                if not iface.startswith("en"):
                    continue
                r2 = subprocess.run(["ifconfig", iface], capture_output=True,
                                    text=True, timeout=3)
                if "status: active" in r2.stdout and "inet " in r2.stdout:
                    m = re.search(r'(\d+)baseT', r2.stdout)
                    if m:
                        return {"type": "ethernet", "ssid": "",
                                "rate": int(m.group(1)),
                                "band": "", "signal": 0}
            return None
        except Exception:
            return None
