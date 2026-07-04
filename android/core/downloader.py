import time, threading, requests
from .constants import CHUNK_SIZE


def _format_speed(bps):
    if bps >= 1024*1024:
        return f"{bps/(1024*1024):.2f} MB/s"
    if bps >= 1024:
        return f"{bps/1024:.2f} KB/s"
    return f"{bps:.1f} B/s"

def _format_bytes(b):
    if b >= 1024*1024*1024:
        return f"{b/(1024*1024*1024):.2f} GB"
    if b >= 1024*1024:
        return f"{b/(1024*1024):.2f} MB"
    if b >= 1024:
        return f"{b/1024:.2f} KB"
    return f"{b} B"

def _fmt_time(sec):
    if sec is None or sec < 0:
        return "--"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s" if h else f"{m:02d}m{s:02d}s"


# Minimum interval between progress callbacks. Without this, a fast single
# stream reads hundreds of chunks per second and floods Kivy's event loop
# with Clock.schedule_once calls. (C3)
_REPORT_INTERVAL = 0.25


class Downloader:

    def __init__(self):
        self.running = False
        self._stop_event = False
        self._gen = 0
        self._on_progress = None
        self._on_complete = None
        self._on_error = None
        self.total_bytes = 0
        self.content_length = 0
        self.max_speed = 0.0
        self.avg_speed = 0.0
        self.realtime_speed = 0.0
        self.start_time = 0
        self._download_start = 0
        self._test_error = False
        self._last_report = 0.0
        self._lock = threading.Lock()

    def start(self, url, workers=6, on_progress=None, on_complete=None,
              on_error=None):
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._on_error = on_error
        self.running = True
        self._stop_event = False
        self._test_error = False
        self._gen += 1
        gen = self._gen
        self.total_bytes = 0
        self.content_length = 0
        self.max_speed = 0.0
        self.avg_speed = 0.0
        self.realtime_speed = 0.0
        self.start_time = time.time()
        self._download_start = self.start_time
        self._last_report = 0.0
        threading.Thread(target=self._task, args=(url, workers, gen),
                         daemon=True).start()

    def stop(self):
        self._stop_event = True
        self.running = False

    def _stopped(self, gen):
        """True if the user stopped or a newer test superseded this one. (B1)"""
        return self._stop_event or gen != self._gen

    def _fail(self, gen, msg):
        """Record a failure and surface it, unless superseded. (A3)"""
        if gen != self._gen:
            return
        self._test_error = True
        if self._on_error:
            self._on_error(msg)

    def _task(self, url, workers, gen):
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

        try:
            if total_size >= 10 * 1024 * 1024 and supports_range:
                range_ok = self._download_range(gen, url, workers, total_size)
                if not range_ok and not self._stopped(gen):
                    # Server ignored the Range header (returned 200). Discard the
                    # partial/duplicated data and restart as a clean single
                    # stream. (A2)
                    with self._lock:
                        self.total_bytes = 0
                        self.max_speed = self.avg_speed = self.realtime_speed = 0.0
                    self._download_start = time.time()
                    self._download_single(gen, url)
            else:
                self._download_single(gen, url)
        except requests.exceptions.Timeout:
            self._fail(gen, "timeout")
        except requests.exceptions.ConnectionError:
            self._fail(gen, "connection_failed")
        except Exception as e:
            self._fail(gen, str(e)[:50])

        if self._stopped(gen):
            return
        self.running = False
        if not self._test_error and self._on_complete:
            self._on_complete()

    def _download_range(self, gen, url, workers, total_size):
        """Segmented parallel download. Returns False if the server did not
        honor Range requests, so the caller can fall back to a single stream."""
        worker_bytes = [0] * workers
        seg_size = total_size // workers
        range_broke = threading.Event()

        def _worker(wid, start, end):
            if start > end:
                return
            try:
                with requests.Session() as s:
                    a = requests.adapters.HTTPAdapter(
                        pool_connections=1, pool_maxsize=1, max_retries=0)
                    s.mount("http://", a)
                    s.mount("https://", a)
                    h = {"Range": f"bytes={start}-{end}"}
                    with s.get(url, stream=True, timeout=(10, 30),
                               headers=h) as r:
                        if r.status_code != 206:
                            # Range not honored; signal fallback instead of
                            # silently contributing 0 bytes. (A2)
                            range_broke.set()
                            return
                        while True:
                            if self._stopped(gen) or range_broke.is_set():
                                break
                            ch = r.raw.read(amt=CHUNK_SIZE,
                                            decode_content=False)
                            if not ch:
                                break
                            worker_bytes[wid] += len(ch)
            except Exception:
                pass

        threads = []
        for i in range(workers):
            s = i * seg_size
            e = total_size - 1 if i == workers - 1 \
                else (i + 1) * seg_size - 1
            t = threading.Thread(target=_worker, args=(i, s, e), daemon=True)
            t.start()
            threads.append(t)

        last_total = 0
        last_time = time.time()
        while not self._stopped(gen):
            if range_broke.is_set():
                break
            if not any(t.is_alive() for t in threads):
                break
            time.sleep(0.5)
            now = time.time()
            total = sum(worker_bytes)
            el = now - last_time
            with self._lock:
                self.total_bytes = total
                if el >= 0.8 and total > last_total:
                    sp = (total - last_total) / el
                    self.realtime_speed = sp
                    if sp > self.max_speed:
                        self.max_speed = sp
                    te = now - self._download_start
                    if te > 0:
                        self.avg_speed = total / te
            if el >= 0.8 and total > last_total:
                last_total = total
                last_time = now
            self._report_progress()

        for t in threads:
            t.join(timeout=2)

        if range_broke.is_set():
            return False

        final_total = sum(worker_bytes)
        with self._lock:
            self.total_bytes = final_total
            te = time.time() - self._download_start
            if te > 0:
                self.avg_speed = final_total / te
        self._report_progress(force=True)

        if not self._stopped(gen):
            # A complete range download must deliver the whole file; anything
            # short is a failure, not a success. (A3)
            if final_total <= 0 or final_total < self.content_length:
                self._fail(gen, "connection_failed")
        return True

    def _download_single(self, gen, url):
        with requests.Session() as s:
            a = requests.adapters.HTTPAdapter(
                pool_connections=1, pool_maxsize=1, max_retries=0)
            s.mount("http://", a)
            s.mount("https://", a)
            with s.get(url, stream=True, timeout=(10, 30)) as r:
                r.raise_for_status()
                last_bytes = 0
                last_time = time.time()
                while True:
                    if self._stopped(gen):
                        break
                    ch = r.raw.read(amt=CHUNK_SIZE, decode_content=False)
                    if not ch:
                        break
                    now = time.time()
                    el = now - last_time
                    with self._lock:
                        self.total_bytes += len(ch)
                        if el >= 0.8:
                            sp = (self.total_bytes - last_bytes) / el
                            self.realtime_speed = sp
                            if sp > self.max_speed:
                                self.max_speed = sp
                            te = now - self._download_start
                            if te > 0:
                                self.avg_speed = self.total_bytes / te
                    if el >= 0.8:
                        last_bytes = self.total_bytes
                        last_time = now
                    self._report_progress()
                with self._lock:
                    te = time.time() - self._download_start
                    if te > 0 and self.total_bytes > 0:
                        self.avg_speed = self.total_bytes / te
                self._report_progress(force=True)
                # Truncated transfer (stream ended before Content-Length) is a
                # failure rather than a silent 100%. (A3)
                if (not self._stopped(gen) and self.content_length > 0
                        and self.total_bytes < self.content_length):
                    self._fail(gen, "connection_failed")

    def _report_progress(self, force=False):
        if not self._on_progress:
            return
        now = time.time()
        # Time-throttle callbacks to avoid flooding the UI event loop. (C3)
        if not force and now - self._last_report < _REPORT_INTERVAL:
            return
        self._last_report = now
        with self._lock:
            tb = self.total_bytes
            rt = self.realtime_speed
            mx = self.max_speed
            av = self.avg_speed
        pct = 0
        if self.content_length > 0:
            pct = min(100, int(tb * 100 / self.content_length))
        self._on_progress({
            "total_bytes": tb,
            "content_length": self.content_length,
            "percent": pct,
            "realtime_speed": rt,
            "max_speed": mx,
            "avg_speed": av,
            "elapsed": now - self._download_start,
        })
