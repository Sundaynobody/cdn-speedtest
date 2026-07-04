import subprocess, platform, os, threading, json, re, glob
from .constants import _HIDE_CONSOLE


class NetworkMixin:

    def _refresh_network_info(self):
        threading.Thread(target=self._fetch_network_task, daemon=True).start()

    @staticmethod
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

    def _run_powershell(self, cmd):
        try:
            ps = "powershell"
            if platform.architecture()[0] == "32bit" and platform.machine().endswith("64"):
                sysnative = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "sysnative",
                                         "WindowsPowerShell", "v1.0", "powershell.exe")
                if os.path.exists(sysnative):
                    ps = sysnative
            r = subprocess.run(
                [ps, "-NoProfile", "-Command", cmd],
                capture_output=True, timeout=10,
                startupinfo=_HIDE_CONSOLE
            )
            out = r.stdout.decode("utf-8", errors="replace").strip().lstrip("\ufeff")
            if r.returncode == 0 and out and out not in ("null", ""):
                # trim outer JSON array/quote markers if present
                if len(out) > 2 and out[0] == '"' and out[-1] == '"':
                    out = out[1:-1]
                elif len(out) > 2 and out[0] == '[' and out[-1] == ']':
                    out = out[1:-1]
                if out and out != "null":
                    return out
        except Exception:
            pass
        return None

    def _win_get_net_info(self):
        """Quick path: netsh first (~0.3s). Fallback: PowerShell for Ethernet."""
        wifi = self._win_get_wifi()
        if wifi:
            return wifi
        return self._ps_get_net_info()

    def _ps_get_net_info(self):
        """PowerShell: default-route + physical adapter (no netsh)."""
        ps = (
            r'$r=@{};$x=Get-NetRoute -DestinationPrefix "0.0.0.0/0"|Sort-Object RouteMetric|'
            r'Select-Object -First 1;if($x){$a=Get-NetAdapter -InterfaceIndex $x.InterfaceIndex;'
            r'$r.default=@{name=$a.Name;speed=$a.LinkSpeed;media=$a.MediaType;virtual=$a.Virtual}};'
            r'$p=Get-NetAdapter -Physical|Where-Object Status -eq "Up"|'
            r'Sort-Object LinkSpeed -Descending|Select-Object -First 1;'
            r'if($p){$r.physical=@{name=$p.Name;speed=$p.LinkSpeed;media=$p.MediaType}};'
            r'$r|ConvertTo-Json -Depth 2 -Compress'
        )
        out = self._run_powershell(ps)
        if not out:
            return None
        try:
            data = json.loads(out)
        except Exception:
            return None

        default = data.get("default")
        physical = data.get("physical")

        if default and not default.get("virtual", True):
            media = default.get("media", "")
            speed = self._parse_speed(default.get("speed", ""))
            if "802.11" in media:
                return {"type": "wifi", "ssid": default.get("name", ""),
                        "rate": speed, "band": "", "name": "Wi-Fi", "signal": 0}
            return {"type": "ethernet", "ssid": "", "rate": speed,
                    "band": "", "name": default.get("name", ""), "signal": 0}

        if physical:
            return {"type": "ethernet", "ssid": "",
                    "rate": self._parse_speed(physical.get("speed", "")),
                    "band": "", "name": physical.get("name", ""), "signal": 0}

        return None

    def _calc_network_refresh_interval(self):
        if self.downloading:
            return 30000
        if self._network_cache["type"] == "unknown":
            return 5000
        return 10000

    def _fetch_network_task(self):
        data = {"type": "unknown", "ssid": "", "rate": 0, "band": "", "name": "", "signal": 0}
        try:
            sys_name = platform.system()
            if sys_name == "Windows":
                data = self._win_get_net_info() or self._win_get_eth() or data
            elif sys_name == "Darwin":
                data = self._mac_get_wifi() or self._mac_get_eth() or data
            else:
                data = self._linux_get_net() or data
        except Exception:
            pass
        self._network_cache = data

        def _schedule_next():
            self._update_network_display()
            if self._network_timer:
                self.root.after_cancel(self._network_timer)
            self._network_timer = self.root.after(
                self._calc_network_refresh_interval(), self._refresh_network_info)

        self.root.after(0, _schedule_next)

    def _update_network_display(self):
        d = self._network_cache
        if d["type"] == "wifi":
            icon = "\U0001F4F6"
            parts = []
            sep = " \u00B7 "
            if d["ssid"]:
                parts.append(d["ssid"])
            if d["rate"] > 0:
                parts.append(f"{d['rate']:.0f} Mbps")
            if d["band"]:
                parts.append(d["band"])
            sig = d.get("signal", 0)
            if sig > 0:
                bars = ("\u2588\u2588\u2588\u2588" if sig > 75 else
                        "\u2588\u2588\u2588 " if sig > 50 else
                        "\u2588\u2588  " if sig > 25 else
                        "\u2588   ")
                parts.append(f"{sig}% {bars}")
        elif d["type"] == "ethernet":
            icon = "\U0001F5A7"
            parts = []
            sep = " \u00B7 "
            if d["rate"] > 0:
                parts.append(f"{d['rate']:.0f} Mbps")
            else:
                parts.append("--")
        else:
            icon = ""
            parts = ["--"]
            sep = ""
        text = sep.join(parts)
        self.net_icon_label.configure(text=icon)
        self.net_label.configure(text=text)

    @staticmethod
    def _parse_wlan_output(text):
        if not text:
            return None
        d = {"type": "wifi", "ssid": "", "rate": 0,
             "band": "", "name": "Wi-Fi", "signal": 0}
        has_ssid = False
        _CHANNEL_KEYS = {"channel", "kanal", "canal", "kana\u0142",
                         "\u043A\u0430\u043D\u0430\u043B", "\u0627\u0644\u0642\u0646\u0627\u0629",
                         "\u901A\u9053", "\u9891\u9053"}
        _SIGNAL_KEYS = {"signal", "\u0441\u0438\u0433\u043D\u0430\u043B",
                        "\u0627\u0644\u0625\u0634\u0627\u0631\u0629",
                        "\u4FE1\u53F7", "\u4FE1\u865F"}
        for line in text.splitlines():
            s = line.strip()
            if ":" not in s:
                continue
            key, val = s.split(":", 1)
            key_lower = key.strip().lower()
            val = val.strip()
            if key_lower == "ssid" and "bssid" not in key_lower:
                d["ssid"] = val
                has_ssid = True
            elif ("mbps" in key_lower or "mbit" in key_lower or "\u043C\u0431\u0438\u0442" in key_lower
                  or "mbps" in val.lower() or "mbit" in val.lower()):
                try:
                    r = float(val.split()[0])
                    if r > d["rate"]:
                        d["rate"] = r
                except ValueError:
                    pass
            elif "ghz" in val.lower() or "\u0433\u0433\u0446" in val.lower():
                # Direct Band field (Win10 2004+): "5 GHz", "2.4 GHz", "6 GHz"
                d["band"] = val
            elif key_lower in _CHANNEL_KEYS:
                try:
                    ch = int(val.split(",")[0].strip())
                    if not d["band"]:
                        d["band"] = "6 GHz" if ch > 165 else (
                            "5 GHz" if ch > 13 else "2.4 GHz")
                except ValueError:
                    pass
            elif key_lower in _SIGNAL_KEYS:
                try:
                    d["signal"] = int(val.rstrip("%"))
                except ValueError:
                    pass
        return d if has_ssid else None

    def _win_get_wifi(self):
        # try 1: direct netsh (fast path, ~0.3s)
        try:
            r = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, timeout=5,
                startupinfo=_HIDE_CONSOLE
            )
            if r.returncode == 0:
                text = r.stdout.decode("oem", errors="replace")
                d = self._parse_wlan_output(text)
                if d:
                    return d
        except Exception:
            pass

        # try 2: via PowerShell (handles encoding / environment quirks)
        out = self._run_powershell("netsh wlan show interfaces")
        if out:
            d = self._parse_wlan_output(out)
            if d:
                return d

        return None

    def _win_get_eth(self):
        out = self._run_powershell(
            r'(Get-NetAdapter -Physical | Where-Object MediaType -EQ "802.3" | '
            r'Select-Object -First 1 Name,LinkSpeed | ConvertTo-Json -Compress)')
        if not out:
            return None
        try:
            obj = json.loads(out)
            return {"type": "ethernet", "ssid": "", "rate": self._parse_speed(obj.get("LinkSpeed", "")),
                    "band": "", "name": obj.get("Name", "Ethernet"), "signal": 0}
        except Exception:
            return None

    def _mac_get_wifi(self):
        try:
            airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            if not os.path.exists(airport):
                airport = "/usr/sbin/airport"
                if not os.path.exists(airport):
                    return None
            r = subprocess.run([airport, "-I"], capture_output=True, text=True, timeout=5)
            if r.returncode != 0:
                return None
            d = {"type": "wifi", "ssid": "", "rate": 0, "band": "", "name": "Wi-Fi", "signal": 0}
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
                        d["band"] = "6 GHz" if ch > 165 else ("5 GHz" if ch > 13 else "2.4 GHz")
                    except Exception:
                        pass
            return d if d["ssid"] else None
        except Exception:
            return None

    def _mac_get_eth(self):
        try:
            r = subprocess.run(["ifconfig", "-l"], capture_output=True, text=True, timeout=3)
            ifaces = r.stdout.strip().split()
            for iface in ifaces:
                if not iface.startswith("en"):
                    continue
                r2 = subprocess.run(["ifconfig", iface], capture_output=True, text=True, timeout=3)
                if "status: active" in r2.stdout and "inet " in r2.stdout:
                    m = re.search(r'(\d+)baseT', r2.stdout)
                    if m:
                        return {"type": "ethernet", "ssid": "", "rate": int(m.group(1)),
                                "band": "", "name": "Ethernet", "signal": 0}
            return None
        except Exception:
            return None

    def _linux_get_net(self):
        try:
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
                    r = subprocess.run(["iw", "dev", name, "link"], capture_output=True, text=True, timeout=5)
                    if r.returncode != 0:
                        continue
                    d = {"type": "wifi", "ssid": "", "rate": 0, "band": "", "name": name, "signal": 0}
                    for line in r.stdout.splitlines():
                        s = line.strip()
                        if s.startswith("SSID:"):
                            d["ssid"] = s.split(":", 1)[1].strip()
                        elif "freq:" in s:
                            try:
                                freq = int(s.split(":")[1].strip().split()[0])
                                d["band"] = "6 GHz" if freq > 6000 else ("5 GHz" if freq > 2500 else "2.4 GHz")
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
                        with open(f"{dev}/speed") as f:
                            speed = int(f.read().strip())
                        if speed > 0:
                            return {"type": "ethernet", "ssid": "", "rate": speed,
                                    "band": "", "name": name, "signal": 0}
                    except Exception:
                        pass
            return None
        except Exception:
            return None
