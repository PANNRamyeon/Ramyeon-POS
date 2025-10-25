
# connectivity.py
import threading, time, requests
from typing import Callable

GEN204 = "https://clients3.google.com/generate_204"

class Connectivity:
    def __init__(self, interval_sec=3):
        self.interval = interval_sec
        self._online = True  # assume online on startup
        self._stop = False
        self._on_online = []
        self._on_offline = []
        self._thread = None
        self._last_state = None
        self._fail_count = 0
        self._ok_count = 0

    def on_online(self, cb: Callable[[], None]): self._on_online.append(cb)
    def on_offline(self, cb: Callable[[], None]): self._on_offline.append(cb)

    def is_online(self): return self._online

    def _emit_online(self):
        for cb in self._on_online: 
            try: cb()
            except Exception: pass

    def _emit_offline(self):
        for cb in self._on_offline:
            try: cb()
            except Exception: pass

    def start(self):
        if self._thread: return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True
        if self._thread: self._thread.join(timeout=1)

    def _run(self):
        while not self._stop:
            try:
                r = requests.get(GEN204, timeout=1.5)
                ok = (r.status_code == 204)
            except Exception:
                ok = False

            if ok:
                self._ok_count += 1
                self._fail_count = 0
                # require 2 consecutive OKs to confirm online
                if not self._online and self._ok_count >= 2:
                    self._online = True
                    self._emit_online()
            else:
                self._fail_count += 1
                self._ok_count = 0
                # require 2 consecutive fails to confirm offline
                if self._online and self._fail_count >= 2:
                    self._online = False
                    self._emit_offline()

            time.sleep(self.interval)
