import subprocess, platform, os, re

try:
    import android
    _ON_ANDROID = True
except ImportError:
    _ON_ANDROID = False


class NetworkMixin:

    def get_network_info(self):
        data = {"type": "unknown", "ssid": "", "rate": 0,
                "band": "", "name": "", "signal": 0}
        try:
            system_name = platform.system()
            if _ON_ANDROID or system_name == "Linux":
                data = self._linux_get_net() or data
            elif system_name == "Darwin":
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

    @staticmethod
    def _dbm_to_percent(dbm):
        if dbm <= -100:
            return 0
        if dbm >= -50:
            return 100
        return int((dbm + 100) * 2)

    @staticmethod
    def _freq_to_band(freq):
        if freq > 6000:
            return "6 GHz"
        if freq > 2500:
            return "5 GHz"
        return "2.4 GHz"

    def _linux_get_net(self):
        try:
            import glob
            for dev in glob.glob("/sys/class/net/*"):
                name = dev.split("/")[-1]
                try:
                    with open(f"{dev}/operstate") as f:
                        op = f.read().strip()
                except Exception:
                    continue
                if op != "up":
                    continue
                if os.path.isdir(f"{dev}/wireless"):
                    d = self._linux_get_wifi(name)
                    if d:
                        return d
                else:
                    try:
                        with open(f"{dev}/speed") as f:
                            speed = int(f.read().strip())
                        if speed > 0:
                            return {"type": "ethernet", "ssid": "",
                                    "rate": speed, "band": "",
                                    "name": name, "signal": 0}
                    except Exception:
                        pass
            return None
        except Exception:
            return None

    def _linux_get_wifi(self, name):
        d = {"type": "wifi", "ssid": "", "rate": 0,
             "band": "", "name": name, "signal": 0}

        self._try_iw(d, name)
        if d["ssid"]:
            return d

        self._try_proc_wireless(d, name)
        if d["ssid"] and d["signal"] > 0:
            return d

        self._try_dumpsys_wifi(d)
        if d["ssid"]:
            return d

        self._try_wpa_cli(d, name)
        if d["ssid"]:
            return d

        return d if d["ssid"] else None

    def _try_iw(self, d, name):
        try:
            r = subprocess.run(["iw", "dev", name, "link"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode != 0:
                return
            for line in r.stdout.splitlines():
                s = line.strip()
                if s.startswith("SSID:"):
                    d["ssid"] = s.split(":", 1)[1].strip()
                elif "freq:" in s:
                    try:
                        freq = int(s.split(":")[1].strip().split()[0])
                        d["band"] = self._freq_to_band(freq)
                    except Exception:
                        pass
                elif "tx bitrate:" in s:
                    m = re.search(r'([\d.]+)\s*MBit/s', s)
                    if m:
                        d["rate"] = float(m.group(1))
                elif "signal:" in s:
                    m = re.search(r'signal:\s*(-?\d+\.?\d*)\s*dBm', s)
                    if m:
                        d["signal"] = self._dbm_to_percent(int(float(m.group(1))))
        except Exception:
            pass

    def _try_proc_wireless(self, d, name):
        try:
            with open("/proc/net/wireless") as f:
                lines = f.readlines()
            for line in lines[2:]:
                parts = line.split()
                if len(parts) < 4:
                    continue
                iface = parts[0].rstrip(":")
                if iface != name:
                    continue
                try:
                    link_quality = int(parts[1])
                    signal_level = int(parts[2])
                    if signal_level < -100:
                        signal_level = -100
                    elif signal_level > 0:
                        signal_level = 0
                    d["signal"] = self._dbm_to_percent(signal_level)
                    if not d["ssid"]:
                        d["ssid"] = name
                    noise = int(parts[3]) if len(parts) > 3 else -92
                    snr = signal_level - noise
                    if snr > 40:
                        d["rate"] = 300
                    elif snr > 25:
                        d["rate"] = 144
                    elif snr > 15:
                        d["rate"] = 54
                    else:
                        d["rate"] = 11
                except (ValueError, IndexError):
                    pass
                break
        except Exception:
            pass

    def _try_dumpsys_wifi(self, d):
        try:
            r = subprocess.run(
                ["dumpsys", "wifi"],
                capture_output=True, text=True, timeout=5)
            if r.returncode != 0:
                return
            in_wifi_info = False
            for line in r.stdout.splitlines():
                s = line.strip()
                if "Wi-Fi is" in s and "enabled" in s:
                    in_wifi_info = True
                    continue
                if in_wifi_info or "mWifiInfo" in s:
                    m = re.search(r'SSID:\s*"?([^",\s]+)"?', s)
                    if m and not d["ssid"]:
                        ssid = m.group(1).strip()
                        if ssid and ssid != "<unknown ssid>":
                            d["ssid"] = ssid
                    m = re.search(r'Link speed:\s*(\d+)\s*(Mbps|kbps)', s)
                    if m:
                        val = float(m.group(1))
                        if m.group(2) == "kbps":
                            val /= 1000
                        d["rate"] = val
                    m = re.search(r'Frequency:\s*(\d+)\s*MHz', s)
                    if m:
                        d["band"] = self._freq_to_band(int(m.group(1)))
                    m = re.search(r'RSSI:\s*(-?\d+)', s)
                    if m:
                        d["signal"] = self._dbm_to_percent(int(m.group(1)))
                    elif not d["signal"]:
                        m = re.search(r'level:\s*(-?\d+)', s)
                        if m:
                            d["signal"] = self._dbm_to_percent(int(m.group(1)))
        except Exception:
            pass

    def _try_wpa_cli(self, d, name):
        try:
            r = subprocess.run(
                ["wpa_cli", "-i", name, "status"],
                capture_output=True, text=True, timeout=5)
            if r.returncode != 0:
                return
            for line in r.stdout.splitlines():
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                if key == "ssid" and not d["ssid"]:
                    d["ssid"] = val.strip().strip('"')
                elif key == "freq":
                    try:
                        d["band"] = self._freq_to_band(int(val.strip()))
                    except ValueError:
                        pass
                elif key == "wpa_state" and val.strip() != "COMPLETED":
                    d["ssid"] = ""
        except Exception:
            pass

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
                 "band": "", "name": "Wi-Fi", "signal": 0}
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
                elif "agrCtlRSSI" in s:
                    try:
                        rssi = int(s.split(":", 1)[1].strip())
                        d["signal"] = self._dbm_to_percent(rssi)
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
                                "band": "", "name": iface, "signal": 0}
            return None
        except Exception:
            return None
