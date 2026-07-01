import time, threading, requests
from tkinter import messagebox
from ttkbootstrap.constants import DISABLED, NORMAL
from .constants import CHUNK_SIZE, UPDATE_INTERVAL
from .i18n import t
from .utils import _format_speed, _format_bytes, _fmt_time


class DownloadMixin:

    def start_test(self):
        if self.downloading: return
        if not self.config["nodes"]:
            messagebox.showwarning("", t("no_nodes"))
            return
        self.downloading = True; self._stop_event = False
        self.start_time = self.last_time = time.time()
        self.total_bytes = self.last_bytes = 0
        self.max_speed = self.avg_speed = self.realtime_speed = 0.0
        self.content_length = 0
        self._test_error = False
        self._test_gen += 1
        gen = self._test_gen
        self.start_btn.configure(state=DISABLED)
        self.stop_btn.configure(state=NORMAL)
        self.settings_btn.configure(state=DISABLED)
        self.pf.pack(fill="x", pady=(0, 6))
        self.progress.configure(value=0)
        self.pct_label.configure(text="0%")
        self._status_key = "testing"; self._status_msg = None
        self.status_label.configure(text=t("testing"), foreground="#2b8a3e")
        self.metric_cards["elapsed"].set_value(_fmt_time(0))
        self.metric_cards["remain"].set_value(t("calculating"))
        threading.Thread(target=self._download_task, daemon=True, args=(gen,)).start()
        self._update_display()

    def stop_test(self):
        self._stop_event = True; self.downloading = False
        self._cleanup_stop()

    def _cleanup_stop(self):
        if self.display_timer:
            self.root.after_cancel(self.display_timer); self.display_timer = None
        self.start_btn.configure(state=NORMAL)
        self.stop_btn.configure(state=DISABLED)
        self.settings_btn.configure(state=NORMAL)
        self.pf.pack_forget()
        if not self._test_error:
            self._status_key = "complete" if not self._stop_event else "stopped"
            self._status_msg = None
            self.status_label.configure(
                text=t(self._status_key),
                foreground="#2b8a3e" if not self._stop_event else "#c92a2a")

    def _download_task(self, gen):
        url = self.config["nodes"][self.current_node_idx]["url"]
        workers = 6

        total_size = 0
        supports_range = False
        try:
            with requests.Session() as s:
                with s.head(url, timeout=10) as r:
                    total_size = int(r.headers.get("Content-Length", 0))
                    if r.headers.get("Accept-Ranges", "").lower() == "bytes":
                        supports_range = True
        except:
            pass
        self.content_length = max(total_size, 0)

        if total_size >= 10 * 1024 * 1024 and supports_range:
            worker_bytes = [0] * workers
            seg_size = total_size // workers

            def _worker(wid, start, end):
                if start > end: return
                try:
                    with requests.Session() as s:
                        a = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
                        s.mount("http://", a); s.mount("https://", a)
                        with s.get(url, stream=True, timeout=(10, 30), headers={"Range": f"bytes={start}-{end}"}) as r:
                            if r.status_code != 206: return
                            while True:
                                if self._stop_event: break
                                ch = r.raw.read(amt=CHUNK_SIZE, decode_content=True)
                                if not ch: break
                                worker_bytes[wid] += len(ch)
                except Exception:
                    pass

            threads = []
            for i in range(workers):
                s = i * seg_size
                e = total_size - 1 if i == workers - 1 else (i + 1) * seg_size - 1
                t = threading.Thread(target=_worker, args=(i, s, e), daemon=True)
                t.start()
                threads.append(t)

            last_total = 0
            last_time = time.time()
            while not self._stop_event:
                if not any(t.is_alive() for t in threads): break
                time.sleep(0.5)
                now = time.time()
                total = sum(worker_bytes)
                self.total_bytes = total
                el = now - last_time
                if el >= 0.8 and total > last_total:
                    sp = (total - last_total) / el
                    self.realtime_speed = sp
                    if sp > self.max_speed: self.max_speed = sp
                    last_total = total; last_time = now
                    te = now - self.start_time
                    if te > 0: self.avg_speed = total / te

            for t in threads: t.join(timeout=2)
            final_total = sum(worker_bytes)
            self.total_bytes = final_total
            te = time.time() - self.start_time
            if te > 0: self.avg_speed = final_total / te
            if final_total <= 0:
                self._test_error = True
                self._status_key = "error"; self._status_msg = None
                self.root.after(0, lambda: self.status_label.configure(text=t("connection_failed"), foreground="#c92a2a"))
        else:
            try:
                with requests.Session() as s:
                    a = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
                    s.mount("http://", a); s.mount("https://", a)
                    with s.get(url, stream=True, timeout=(10, 30)) as r:
                        r.raise_for_status()
                        while True:
                            if self._stop_event: break
                            ch = r.raw.read(amt=CHUNK_SIZE, decode_content=True)
                            if not ch: break
                            now = time.time(); self.total_bytes += len(ch)
                            el = now - self.last_time
                            if el >= 0.8:
                                sp = (self.total_bytes - self.last_bytes) / el
                                self.realtime_speed = sp
                                if sp > self.max_speed: self.max_speed = sp
                                self.last_bytes = self.total_bytes; self.last_time = now
                                te = now - self.start_time
                                if te > 0: self.avg_speed = self.total_bytes / te
                        te = time.time() - self.start_time
                        if te > 0: self.avg_speed = self.total_bytes / te
            except requests.exceptions.Timeout:
                self._test_error = True
                self._status_key = "timeout"; self._status_msg = None
                self.root.after(0, lambda: self.status_label.configure(text=t("timeout"), foreground="#c92a2a"))
            except requests.exceptions.ConnectionError:
                self._test_error = True
                self._status_key = "connection_failed"; self._status_msg = None
                self.root.after(0, lambda: self.status_label.configure(text=t("connection_failed"), foreground="#c92a2a"))
            except Exception as e:
                self._test_error = True
                self._status_key = "error"; self._status_msg = str(e)[:50]
                m = self._status_msg
                self.root.after(0, lambda msg=m: self.status_label.configure(text=t("error", msg=msg), foreground="#c92a2a"))
        self.root.after(0, lambda g=gen: self._finish_test(g))

    def _finish_test(self, gen):
        if gen != self._test_gen or self._stop_event: return
        self.downloading = False
        self._cleanup_stop()
        if self._status_key == "complete":
            self._auto_export_report()

    def _update_display(self):
        if not self.downloading: return
        now = time.time(); el = now - self.start_time
        self.metric_cards["realtime"].set_value(_format_speed(self.realtime_speed))
        self.metric_cards["max"].set_value(_format_speed(self.max_speed))
        self.metric_cards["avg"].set_value(_format_speed(self.avg_speed))
        self.metric_cards["elapsed"].set_value(_fmt_time(el))
        self.metric_cards["downloaded"].set_value(_format_bytes(self.total_bytes))
        if self.content_length > 0:
            pct = min(100, int(self.total_bytes * 100 / self.content_length))
            self.progress.configure(value=pct)
            self.pct_label.configure(text=f"{pct}%")
        else:
            self.pct_label.configure(text="")
        if self.realtime_speed > 0:
            if self.content_length > 0:
                rm = max(0, self.content_length - self.total_bytes) / self.realtime_speed
            elif self.total_bytes > 0:
                rm = max(0, self.total_bytes / self.realtime_speed - el)
            else: rm = None
            self.metric_cards["remain"].set_value(_fmt_time(rm))
        else:
            self.metric_cards["remain"].set_value(t("calculating"))
        self.display_timer = self.root.after(UPDATE_INTERVAL, self._update_display)
