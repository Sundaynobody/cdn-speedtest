import os, json, platform
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.lang import Builder
from kivy.utils import platform as kivy_platform

from core.constants import VERSION, DEFAULT_CONFIG, CONFIG_FILE
from core.i18n import t, set_language, LANG, _supported_langs
from core.ip_location import get_ip_info
from core.network import NetworkMixin
from core.downloader import Downloader, _format_speed, _format_bytes, _fmt_time


def get_config_dir():
    if kivy_platform == "android":
        from android.storage import app_storage_path
        p = os.path.join(app_storage_path(), ".cdn_speedtest")
    else:
        p = os.path.join(os.path.expanduser("~"), ".cdn_speedtest")
    os.makedirs(p, exist_ok=True)
    return p


def load_config():
    path = os.path.join(get_config_dir(), CONFIG_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                nodes = data.get("nodes", [])
                if isinstance(nodes, list) and len(nodes) > 0:
                    valid = [n for n in nodes
                             if isinstance(n, dict) and "name" in n and "url" in n]
                    return {
                        "defaultIndex": data.get("defaultIndex", 0),
                        "language": data.get("language", "en"),
                        "nodes": valid or [dict(n) for n in DEFAULT_CONFIG["nodes"]],
                    }
        except Exception:
            pass
    return {
        "defaultIndex": DEFAULT_CONFIG["defaultIndex"],
        "language": DEFAULT_CONFIG["language"],
        "nodes": [dict(n) for n in DEFAULT_CONFIG["nodes"]],
    }


def save_config(config):
    path = os.path.join(get_config_dir(), CONFIG_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class MainScreen(Screen):
    ip_text = StringProperty("")
    location_text = StringProperty("")
    network_text = StringProperty("")
    status_text = StringProperty("")
    node_name = StringProperty("")
    node_count = NumericProperty(0)
    progress_pct = NumericProperty(0)
    btn_start_text = StringProperty("")
    btn_start_disabled = False
    btn_stop_disabled = True

    def __init__(self, **kw):
        super().__init__(**kw)
        self._net = NetworkMixin()
        self._dl = Downloader()
        self._dl_task = None
        self._config = load_config()
        set_language(self._config.get("language", "en"))
        self._current_node = 0
        self._refresh_ui()

    def on_enter(self):
        self._fetch_ip()
        self._fetch_network()
        Clock.schedule_interval(self._tick_network, 30)

    def on_leave(self):
        Clock.unschedule(self._tick_network)

    def _refresh_ui(self):
        self.btn_start_text = t("start_test")
        ns = self._config["nodes"]
        self.node_count = len(ns)
        idx = self._config["defaultIndex"]
        if 0 <= idx < len(ns):
            self._current_node = idx
            self.node_name = ns[idx]["name"]
        self.status_text = t("ready")

    def _fetch_ip(self):
        self.ip_text = t("fetching")
        get_ip_info(self._on_ip_result)

    def _on_ip_result(self, ip, loc):
        self.ip_text = ip
        self.location_text = loc

    def _fetch_network(self):
        info = self._net.get_network_info()
        parts = []
        if info["type"] == "wifi" and info["ssid"]:
            parts.append(info["ssid"])
        if info["rate"] > 0:
            parts.append(f"{info['rate']:.0f} Mbps")
        self.network_text = " \u00B7 ".join(parts) if parts else "--"

    def _tick_network(self, dt):
        self._fetch_network()

    def on_nodes_updated(self, config):
        self._config = config
        set_language(config.get("language", "en"))
        self._refresh_ui()
        self._fetch_ip()
        self._fetch_network()

    def open_settings(self):
        sm = self.manager
        s = sm.get_screen("settings")
        s.load_config(self._config)
        sm.current = "settings"

    def start_test(self):
        ns = self._config["nodes"]
        if not ns:
            self.status_text = t("no_nodes")
            return
        idx = self._current_node
        if idx < 0 or idx >= len(ns):
            idx = 0
        url = ns[idx]["url"]
        self.status_text = t("testing")
        self.progress_pct = 0
        self._dl.start(
            url,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

    def stop_test(self):
        self._dl.stop()
        self.status_text = t("stopped")

    def _on_progress(self, data):
        def update(dt, d=data):
            self.progress_pct = d["percent"]
            if hasattr(self, "card_realtime"):
                self.card_realtime = _format_speed(d["realtime_speed"])
            if hasattr(self, "card_max"):
                self.card_max = _format_speed(d["max_speed"])
            if hasattr(self, "card_avg"):
                self.card_avg = _format_speed(d["avg_speed"])
            if hasattr(self, "card_downloaded"):
                self.card_downloaded = _format_bytes(d["total_bytes"])
            if hasattr(self, "card_elapsed"):
                self.card_elapsed = _fmt_time(d["elapsed"])
            if hasattr(self, "card_remain"):
                remain = "--"
                if self._dl.content_length > 0 and d["realtime_speed"] > 0:
                    rm = max(0, self._dl.content_length - d["total_bytes"]) / \
                         d["realtime_speed"]
                    remain = _fmt_time(rm)
                elif d["total_bytes"] > 0 and d["realtime_speed"] > 0:
                    rm = max(0, d["total_bytes"] / d["realtime_speed"] -
                             d["elapsed"])
                    remain = _fmt_time(rm)
                self.card_remain = remain
        Clock.schedule_once(update)

    def _on_complete(self):
        def update(dt):
            self.status_text = t("complete")
            self.progress_pct = 100
        Clock.schedule_once(update)

    def _on_error(self, msg):
        def update(dt, m=msg):
            if m == "timeout":
                self.status_text = t("timeout")
            elif m == "connection_failed":
                self.status_text = t("connection_failed")
            else:
                self.status_text = t("error", msg=m)
        Clock.schedule_once(update)


class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._config = None

    def load_config(self, config):
        self._config = config

    def get_config(self):
        return self._config

    def switch_language(self, lang_code):
        if self._config:
            self._config["language"] = lang_code
            set_language(lang_code)
            save_config(self._config)

    def go_back(self):
        self.manager.current = "main"
        ms = self.manager.get_screen("main")
        ms.on_nodes_updated(self._config)


class CDNSpeedTestApp(App):
    def build(self):
        self.title = f"CDN SpeedTest v{VERSION}"
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm


if __name__ == "__main__":
    CDNSpeedTestApp().run()
