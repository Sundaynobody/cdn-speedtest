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
        self._download_start = self.start_time
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

    def _stopped(self, gen):
        """True if the user stopped or a newer test superseded this one. (B1)"""
        return self._stop_event or gen != self._test_gen

    def _fail(self, gen, key, msg=None):
        """Record a test failure and surface it on the status line. (A3)"""
        if gen != self._test_gen:
            return
        self._test_error = True
        self._status_key = key
        self._status_msg = msg
        text = t("error", msg=msg) if key == "error" and msg else t(key)
        self.root.after(0, lambda tx=text: self.status_label.configure(
            text=tx, foreground="#c92a2a"))

    def _download_task(self, gen):
        url = self.config["nodes"][self.current_node_idx]["url"]
        workers = 6

        total_size = 0
        supports_range = False
        try:
            with requests.Session() as s:
                with s.head(url, timeout=10) as r:
                    total_size = int(r.headers.get("Content-Length", 0))
                    ar = r.headers.get("Accept-Ranges", "").lower()
                    if ar and ar != "none" and "bytes" in ar:
                        supports_range = True
                    if not supports_range and total_size > 0:
                        with s.get(url, stream=True, timeout=10,
                                  headers={"Range": "bytes=0-0"}) as r2:
                            if r2.status_code == 206:
                                supports_range = True
        except Exception:
            pass
        self.content_length = max(total_size, 0)

        # Data transfer starts now. Reset the throughput baseline so the probe
        # latency above (HEAD + range check, up to ~10s) is not counted against
        # the average speed. (A1)
        self._download_start = time.time()

        if total_size >= 10 * 1024 * 1024 and supports_range:
            range_ok = self._download_multi(gen, url, workers, total_size)
            if not range_ok and not self._stopped(gen):
                # Server ignored the Range header (returned 200). Rather than
                # trust the partial/duplicated data, restart as a clean single
                # stream. (A2)
                with self._stats_lock:
                    self.total_bytes = self.last_bytes = 0
                    self.max_speed = self.avg_speed = self.realtime_speed = 0.0
                self._download_start = time.time()
                self._download_stream(gen, url)
        else:
            self._download_stream(gen, url)

        self.root.after(0, lambda g=gen: self._finish_test(g))

    def _download_multi(self, gen, url, workers, total_size):
        """Segmented parallel download. Returns False if the server did not
        honor Range requests, so the caller can fall back to a single stream."""
        worker_bytes = [0] * workers
        seg_size = total_size // workers
        range_broke = threading.Event()

        def _worker(wid, start, end):
            if start > end: return
            try:
                with requests.Session() as s:
                    a = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
                    s.mount("http://", a); s.mount("https://", a)
                    with s.get(url, stream=True, timeout=(10, 30), headers={"Range": f"bytes={start}-{end}"}) as r:
                        if r.status_code != 206:
                            # Range not honored; signal fallback instead of
                            # silently contributing 0 bytes. (A2)
                            range_broke.set()
                            return
                        while True:
                            if self._stopped(gen) or range_broke.is_set(): break
                            ch = r.raw.read(amt=CHUNK_SIZE, decode_content=False)
                            if not ch: break
                            worker_bytes[wid] += len(ch)
            except Exception:
                pass

        threads = []
        for i in range(workers):
            s = i * seg_size
            e = total_size - 1 if i == workers - 1 else (i + 1) * seg_size - 1
            th = threading.Thread(target=_worker, args=(i, s, e), daemon=True)
            th.start()
            threads.append(th)

        last_total = 0
        last_time = time.time()
        while not self._stopped(gen):
            if range_broke.is_set(): break
            if not any(t.is_alive() for t in threads): break
            time.sleep(0.5)
            now = time.time()
            total = sum(worker_bytes)
            el = now - last_time
            with self._stats_lock:
                self.total_bytes = total
                if el >= 0.8 and total > last_total:
                    sp = (total - last_total) / el
                    self.realtime_speed = sp
                    if sp > self.max_speed: self.max_speed = sp
                    te = now - self._download_start
                    if te > 0: self.avg_speed = total / te
            if el >= 0.8 and total > last_total:
                last_total = total; last_time = now

        for th in threads: th.join(timeout=2)

        if range_broke.is_set():
            return False

        final_total = sum(worker_bytes)
        with self._stats_lock:
            self.total_bytes = final_total
            te = time.time() - self._download_start
            if te > 0: self.avg_speed = final_total / te

        if not self._stopped(gen):
            # A complete range download must deliver the whole file; anything
            # short is a failure, not a success. (A3)
            if final_total <= 0 or final_total < self.content_length:
                self._fail(gen, "connection_failed")
        return True

    def _download_stream(self, gen, url):
        try:
            with requests.Session() as s:
                a = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
                s.mount("http://", a); s.mount("https://", a)
                with s.get(url, stream=True, timeout=(10, 30)) as r:
                    r.raise_for_status()
                    last_bytes = 0
                    last_time = time.time()
                    while True:
                        if self._stopped(gen): break
                        ch = r.raw.read(amt=CHUNK_SIZE, decode_content=False)
                        if not ch: break
                        now = time.time()
                        el = now - last_time
                        with self._stats_lock:
                            self.total_bytes += len(ch)
                            if el >= 0.8:
                                sp = (self.total_bytes - last_bytes) / el
                                self.realtime_speed = sp
                                if sp > self.max_speed: self.max_speed = sp
                                te = now - self._download_start
                                if te > 0: self.avg_speed = self.total_bytes / te
                        if el >= 0.8:
                            last_bytes = self.total_bytes; last_time = now
                    with self._stats_lock:
                        te = time.time() - self._download_start
                        if te > 0 and self.total_bytes > 0:
                            self.avg_speed = self.total_bytes / te
                    # Truncated transfer (stream ended before Content-Length)
                    # is a failure rather than a silent 100%. (A3)
                    if (not self._stopped(gen) and self.content_length > 0
                            and self.total_bytes < self.content_length):
                        self._fail(gen, "connection_failed")
        except requests.exceptions.Timeout:
            self._fail(gen, "timeout")
        except requests.exceptions.ConnectionError:
            self._fail(gen, "connection_failed")
        except Exception as e:
            self._fail(gen, "error", str(e)[:50])

    def _finish_test(self, gen):
        if gen != self._test_gen or self._stop_event: return
        with self._stats_lock:
            rt, mx, av, tb = (self.realtime_speed, self.max_speed,
                              self.avg_speed, self.total_bytes)
        self.metric_cards["realtime"].set_value(_format_speed(rt))
        self.metric_cards["max"].set_value(_format_speed(mx))
        self.metric_cards["avg"].set_value(_format_speed(av))
        self.metric_cards["elapsed"].set_value(_fmt_time(time.time() - self.start_time))
        self.metric_cards["downloaded"].set_value(_format_bytes(tb))
        self.metric_cards["remain"].set_value("--")
        if self.content_length > 0:
            pct = min(100, int(tb * 100 / self.content_length))
            self.progress.configure(value=pct)
            self.pct_label.configure(text=f"{pct}%")
        else:
            self.pct_label.configure(text="")
        self.downloading = False
        self._cleanup_stop()
        if self._status_key == "complete":
            self._auto_export_report()

    def _update_display(self):
        if not self.downloading: return
        now = time.time(); el = now - self.start_time
        with self._stats_lock:
            rt, mx, av, tb = (self.realtime_speed, self.max_speed,
                              self.avg_speed, self.total_bytes)
        self.metric_cards["realtime"].set_value(_format_speed(rt))
        self.metric_cards["max"].set_value(_format_speed(mx))
        self.metric_cards["avg"].set_value(_format_speed(av))
        self.metric_cards["elapsed"].set_value(_fmt_time(el))
        self.metric_cards["downloaded"].set_value(_format_bytes(tb))
        if self.content_length > 0:
            pct = min(100, int(tb * 100 / self.content_length))
            self.progress.configure(value=pct)
            self.pct_label.configure(text=f"{pct}%")
        else:
            self.pct_label.configure(text="")
        if rt > 0:
            if self.content_length > 0:
                rm = max(0, self.content_length - tb) / rt
            elif tb > 0:
                rm = max(0, tb / rt - el)
            else: rm = None
            self.metric_cards["remain"].set_value(_fmt_time(rm))
        else:
            self.metric_cards["remain"].set_value(t("calculating"))
        self.display_timer = self.root.after(UPDATE_INTERVAL, self._update_display)
