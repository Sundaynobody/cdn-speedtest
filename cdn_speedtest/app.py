import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import time, os, json, sys, platform

from . import constants
from .i18n import t, set_language
from .utils import (
    get_config_dir, get_dpi_factor, resource_path, set_window_icon,
    _get_monitor_dpi, load_config, save_config,
    _format_speed, _format_bytes, _fmt_time,
)
from .network import NetworkMixin
from .ip_location import IpLocationMixin
from .downloader import DownloadMixin
from .widgets import MetricCard, SettingsDialog
from .constants import VERSION, _IP_CACHE, THEME, _UI_FONT, _MONO_FONT


class SpeedTester(NetworkMixin, IpLocationMixin, DownloadMixin):
    def __init__(self, root, dpi=96):
        self.root = root
        self.dpi = dpi
        self.config = load_config()
        set_language(self.config.get("language", "en"))
        sf = dpi / 96.0
        self.root.geometry(f"{int(620*sf)}x{int(520*sf)}")
        self.root.resizable(False, False)
        set_window_icon(self.root)
        self.current_node_idx = self._clamp(self.config["defaultIndex"])
        self.downloading = False
        self._stop_event = False
        self._test_error = False
        self._test_gen = 0
        self._status_key = "ready"
        self._status_msg = None
        self.start_time = 0
        self.total_bytes = 0
        self.last_bytes = 0
        self.last_time = 0
        self.max_speed = 0.0
        self.avg_speed = 0.0
        self.realtime_speed = 0.0
        self.content_length = 0
        self.display_timer = None
        self.metric_cards = {}
        self._speed_frame = None
        self._network_timer = None
        self._ip_timer = None
        self._network_cache = {"type": "unknown", "ssid": "", "rate": 0, "band": "", "name": "", "signal": 0}
        self._setup_ui()

    def _clamp(self, idx):
        ns = self.config["nodes"]
        return 0 if idx < 0 or idx >= len(ns) else idx

    def _setup_ui(self):
        self.root.title(t("app_title", VERSION=VERSION))
        main = tb.Frame(self.root)
        main.pack(fill="both", expand=True, padx=16, pady=16)

        ic = tb.LabelFrame(main, text="")
        ic.pack(fill="x", pady=(0, 10))
        ir = tb.Frame(ic); ir.pack(fill="x", padx=12, pady=(8, 4))
        self.ip_title_label = tb.Label(ir, text=t("ip_address"),
                                        font=(_UI_FONT, 8),
                                        foreground="#999")
        self.ip_title_label.pack(side="left")
        bf = tb.Frame(ir); bf.pack(side="right")
        self.settings_btn = tb.Button(bf, text=t("settings"),
                                       command=self._open_settings,
                                       bootstyle="secondary,outline")
        self.settings_btn.pack(side="left", padx=2)
        self.stop_btn = tb.Button(bf, text=t("stop"),
                                   command=self.stop_test,
                                   bootstyle="danger,outline", state=DISABLED)
        self.stop_btn.pack(side="left", padx=2)
        self.start_btn = tb.Button(bf, text=t("start_test"),
                                    command=self.start_test,
                                    bootstyle="success")
        self.start_btn.pack(side="left", padx=2)
        iv = tb.Frame(ic); iv.pack(fill="x", padx=12, pady=(2, 8))
        self.ip_label = tb.Label(iv, text=t("fetching"),
                                 font=(_MONO_FONT, 16, "bold"))
        self.ip_label.pack(side="left")
        self.location_label = tb.Label(iv, text="",
                                        font=(_UI_FONT, 9),
                                        foreground="#999")
        self.location_label.pack(side="left", padx=(12,0), pady=(4,0))

        nv = tb.Frame(ic); nv.pack(fill="x", padx=12, pady=(0, 6))
        self.net_icon_label = tb.Label(nv, text="", font=(_UI_FONT, 12))
        self.net_icon_label.pack(side="left")
        self.net_label = tb.Label(nv, text="",
                                   font=(_UI_FONT, 9), foreground="#999")
        self.net_label.pack(side="left", padx=(4, 0))

        self._speed_frame = tb.LabelFrame(main, text=f"  {t('speed_results')}  ")
        self._speed_frame.pack(fill="both", expand=True, pady=(0, 10),
                               ipadx=12, ipady=12)
        gd = tb.Frame(self._speed_frame)
        gd.pack(fill="both", expand=True, padx=4, pady=4)

        self.card_keys = [("realtime_speed","realtime"),("max_speed","max"),
                          ("avg_speed","avg"),("elapsed","elapsed"),
                          ("remaining","remain"),("downloaded","downloaded")]
        for i, (lk, key) in enumerate(self.card_keys):
            r, c = i // 3, i % 3
            card = MetricCard(gd, "--")
            card.set_title(t(lk))
            card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            gd.columnconfigure(c, weight=1)
            self.metric_cards[key] = card
        gd.rowconfigure(0, weight=1); gd.rowconfigure(1, weight=1)

        self.pf = tb.Frame(main)
        self.progress = tb.Progressbar(self.pf, mode="determinate", bootstyle=INFO)
        self.progress.pack(side="left", fill="x", expand=True)
        self.pct_label = tb.Label(self.pf, text="", font=(_UI_FONT, 9))
        self.pct_label.pack(side="right", padx=(4, 0))

        sf2 = tb.Frame(main); sf2.pack(fill="x")
        self.status_label = tb.Label(sf2, text=t("ready"),
                                     font=(_UI_FONT, 8),
                                     foreground="#999")
        self.status_label.pack(side="left")
        self.export_btn = tb.Button(sf2, text=t("export"), command=self._export_report,
                                     bootstyle="secondary,outline", padding=(2,0))
        self.export_btn.pack(side="right", padx=(0, 4))
        tb.Label(sf2, text=f"v{VERSION}",
                 font=(_UI_FONT, 8),
                 foreground="#ccc").pack(side="right")
        self._fetch_ip_info()
        self._refresh_network_info()

    def _apply_language(self):
        self.root.title(t("app_title", VERSION=VERSION))
        self.ip_title_label.configure(text=t("ip_address"))
        self.settings_btn.configure(text=t("settings"))
        self.export_btn.configure(text=t("export"))
        self.stop_btn.configure(text=t("stop"))
        self.start_btn.configure(text=t("start_test"))
        self._speed_frame.configure(text=f"  {t('speed_results')}  ")
        for lk, key in self.card_keys:
            self.metric_cards[key].set_title(t(lk))
        sk, sm = self._status_key, self._status_msg
        if sk == "error" and sm:
            self.status_label.configure(text=t(sk, msg=sm))
        else:
            self.status_label.configure(text=t(sk))

    def _open_settings(self):
        SettingsDialog(self.root, self.config, self._on_config_updated)

    def _on_config_updated(self, config):
        self.config = config
        set_language(config.get("language", "en"))
        self.current_node_idx = self._clamp(config["defaultIndex"])
        self._apply_language()

    def _build_report_data(self):
        nc = self._network_cache
        node = self.config["nodes"][self.current_node_idx]
        net_info = {"type": nc["type"]}
        if nc["type"] == "wifi":
            net_info["ssid"] = nc.get("ssid", "")
            net_info["rate_mbps"] = nc.get("rate", 0)
            net_info["band"] = nc.get("band", "")
            net_info["signal_percent"] = nc.get("signal", 0)
        elif nc["type"] == "ethernet":
            net_info["rate_mbps"] = nc.get("rate", 0)
        return {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": VERSION,
            "ip_info": {
                "address": self.ip_label.cget("text"),
                "location": self.location_label.cget("text"),
                "asn": _IP_CACHE.get("asn", 0),
            },
            "network": net_info,
            "speed_test": {
                "node": node["name"],
                "url": node["url"],
                "status": self.status_label.cget("text"),
                "results": {
                    "realtime": self.metric_cards["realtime"].value_label.cget("text"),
                    "max": self.metric_cards["max"].value_label.cget("text"),
                    "avg": self.metric_cards["avg"].value_label.cget("text"),
                    "downloaded": self.metric_cards["downloaded"].value_label.cget("text"),
                    "elapsed": self.metric_cards["elapsed"].value_label.cget("text"),
                    "remaining": self.metric_cards["remain"].value_label.cget("text"),
                },
                "raw": {
                    "realtime_bps": round(self.realtime_speed),
                    "max_bps": round(self.max_speed),
                    "avg_bps": round(self.avg_speed),
                    "total_bytes": self.total_bytes,
                },
            },
        }

    def _save_report(self, path, report):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def _export_report(self):
        default_name = f"CDNSpeedTest_Report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_name, title=os.path.basename(default_name))
        if path:
            try:
                self._save_report(path, self._build_report_data())
                orig = self.status_label.cget("text")
                self.status_label.configure(text=f"\u2713 {os.path.basename(path)}", foreground="#2b8a3e")
                self.root.after(3000, lambda t=orig: self.status_label.configure(text=t, foreground="#999"))
            except Exception as e:
                messagebox.showerror("", f"Export failed:\n{e}")

    def _auto_export_report(self):
        d = self._build_report_data()
        ts = time.strftime("%Y%m%d_%H%M%S")
        name = f"CDNSpeedTest_Report_{ts}.json"
        path = os.path.join(os.getcwd(), name)
        try:
            self._save_report(path, d)
        except Exception:
            pass


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        print(f"CDNSpeedTest v{VERSION}")
        return
    root = tk.Tk()
    if platform.system() == "Windows":
        dpi = _get_monitor_dpi()
        root.tk.call("tk", "scaling", dpi / 72.0)
    else:
        try:
            dpi = int(root.winfo_fpixels('1i'))
        except Exception:
            dpi = 96
    tb.Style(theme=THEME)
    SpeedTester(root, dpi)
    root.mainloop()
