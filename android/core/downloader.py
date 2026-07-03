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


class Downloader:

    def __init__(self):
        self.running = False
        self._stop_event = False
        self._on_progress = None
        self._on_complete = None
        self._on_error = None
        self.total_bytes = 0
        self.content_length = 0
        self.max_speed = 0.0
        self.avg_speed = 0.0
        self.realtime_speed = 0.0
        self.start_time = 0

    def start(self, url, workers=6, on_progress=None, on_complete=None,
              on_error=None):
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._on_error = on_error
        self.running = True
        self._stop_event = False
        self.total_bytes = 0
        self.content_length = 0
        self.max_speed = 0.0
        self.avg_speed = 0.0
        self.realtime_speed = 0.0
        self.start_time = time.time()
        threading.Thread(target=self._task, args=(url, workers),
                         daemon=True).start()

    def stop(self):
        self._stop_event = True
        self.running = False

    def _task(self, url, workers):
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

        try:
            if total_size >= 10 * 1024 * 1024 and supports_range:
                self._download_range(url, workers, total_size)
            else:
                self._download_single(url)
        except requests.exceptions.Timeout:
            self.running = False
            if self._on_error:
                self._on_error("timeout")
            return
        except requests.exceptions.ConnectionError:
            self.running = False
            if self._on_error:
                self._on_error("connection_failed")
            return
        except Exception as e:
            self.running = False
            if self._on_error:
                self._on_error(str(e)[:50])
            return

        self.running = False
        if not self._stop_event and self._on_complete:
            self._on_complete()

    def _download_range(self, url, workers, total_size):
        worker_bytes = [0] * workers
        seg_size = total_size // workers

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
                            return
                        while True:
                            if self._stop_event:
                                break
                            ch = r.raw.read(amt=CHUNK_SIZE,
                                            decode_content=True)
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
        while not self._stop_event:
            if not any(t.is_alive() for t in threads):
                break
            time.sleep(0.5)
            now = time.time()
            total = sum(worker_bytes)
            self.total_bytes = total
            el = now - last_time
            if el >= 0.8 and total > last_total:
                sp = (total - last_total) / el
                self.realtime_speed = sp
                if sp > self.max_speed:
                    self.max_speed = sp
                last_total = total
                last_time = now
                te = now - self.start_time
                if te > 0:
                    self.avg_speed = total / te
            self._report_progress()

        for t in threads:
            t.join(timeout=2)
        final_total = sum(worker_bytes)
        self.total_bytes = final_total
        if 0 < final_total < self.content_length:
            self.content_length = final_total
        te = time.time() - self.start_time
        if te > 0:
            self.avg_speed = final_total / te
        self._report_progress()

    def _download_single(self, url):
        with requests.Session() as s:
            a = requests.adapters.HTTPAdapter(
                pool_connections=1, pool_maxsize=1, max_retries=0)
            s.mount("http://", a)
            s.mount("https://", a)
            with s.get(url, stream=True, timeout=(10, 30)) as r:
                r.raise_for_status()
                last_bytes = 0
                last_time = time.time()
                start_time = self.start_time
                while True:
                    if self._stop_event:
                        break
                    ch = r.raw.read(amt=CHUNK_SIZE, decode_content=True)
                    if not ch:
                        break
                    now = time.time()
                    self.total_bytes += len(ch)
                    el = now - last_time
                    if el >= 0.8:
                        sp = (self.total_bytes - last_bytes) / el
                        self.realtime_speed = sp
                        if sp > self.max_speed:
                            self.max_speed = sp
                        last_bytes = self.total_bytes
                        last_time = now
                        te = now - start_time
                        if te > 0:
                            self.avg_speed = self.total_bytes / te
                    self._report_progress()
                if self.total_bytes < self.content_length:
                    self.content_length = self.total_bytes
                te = time.time() - start_time
                if te > 0:
                    self.avg_speed = self.total_bytes / te
                self._report_progress()

    def _report_progress(self):
        if self._on_progress:
            pct = 0
            if self.content_length > 0:
                pct = min(100, int(self.total_bytes * 100 /
                                   self.content_length))
            self._on_progress({
                "total_bytes": self.total_bytes,
                "content_length": self.content_length,
                "percent": pct,
                "realtime_speed": self.realtime_speed,
                "max_speed": self.max_speed,
                "avg_speed": self.avg_speed,
                "elapsed": time.time() - self.start_time,
            })
