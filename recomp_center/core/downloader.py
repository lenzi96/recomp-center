"""Asynchronous download worker for Recomp Center."""

import os
import time
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal


def format_size(bytes_val: int) -> str:
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


class DownloadWorker(QThread):
    progress = pyqtSignal(int, int, str)  # current_bytes, total_bytes, speed_str
    status = pyqtSignal(str)              # status message
    finished = pyqtSignal(str)            # downloaded_file_path
    error = pyqtSignal(str)               # error message

    def __init__(self, url: str, target_dir: str, filename: str, headers: dict = None):
        super().__init__()
        self.url = url
        self.target_dir = target_dir
        self.filename = filename
        self.headers = headers or {"User-Agent": "Recomp-Center/1.0"}
        self._is_cancelled = False
        self.target_path = os.path.join(target_dir, filename)

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        os.makedirs(self.target_dir, exist_ok=True)
        self.status.emit(f"Verbindung wird aufgebaut: {self.filename}...")

        try:
            req = urllib.request.Request(self.url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 64 * 1024  # 64 KB chunks

                start_time = time.time()
                last_update_time = start_time
                last_downloaded = 0

                with open(self.target_path, "wb") as out_file:
                    while True:
                        if self._is_cancelled:
                            out_file.close()
                            if os.path.exists(self.target_path):
                                try:
                                    os.remove(self.target_path)
                                except Exception:
                                    pass
                            self.status.emit("Download abgebrochen.")
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        out_file.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if now - last_update_time >= 0.25:
                            elapsed = now - last_update_time
                            bytes_diff = downloaded - last_downloaded
                            speed = bytes_diff / elapsed if elapsed > 0 else 0
                            speed_str = f"{format_size(int(speed))}/s"
                            self.progress.emit(downloaded, total_size, speed_str)
                            last_update_time = now
                            last_downloaded = downloaded

                # Final 100% update
                self.progress.emit(downloaded, total_size or downloaded, "Fertig")
                self.status.emit("Download erfolgreich abgeschlossen.")
                self.finished.emit(self.target_path)

        except Exception as e:
            if os.path.exists(self.target_path):
                try:
                    os.remove(self.target_path)
                except Exception:
                    pass
            self.error.emit(f"Fehler beim Herunterladen: {str(e)}")
