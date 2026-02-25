# analysis.py
# ─────────────────────────────────────────────────────────────────────────────
# CrowdAnalyzer – counts people, classifies density, and raises alerts.
# ─────────────────────────────────────────────────────────────────────────────

import csv
import os
from datetime import datetime
import config

class CrowdAnalyzer:
    """
    Stateless helper that converts a list of confirmed tracks into:
        - person count
        - density label
        - alert flag
        - peak count
        - wait time (gamified)
        - mode-specific messages

    Optionally logs each reading to a CSV file.
    """

    def __init__(self, mode: str = config.CURRENT_MODE):
        self.mode = mode
        self.config = config.MODE_CONFIGS.get(mode, config.MODE_CONFIGS["canteen"])
        
        self.low_threshold   = self.config["low_threshold"]
        self.high_threshold  = self.config["high_threshold"]
        self.alert_threshold = self.config["alert_threshold"]
        self.labels          = self.config["labels"]
        
        self.peak_count = 0

        # CSV logging setup
        self._csv_ready = False
        if config.ENABLE_CSV_LOGGING:
            self._init_csv(config.CSV_FILE_PATH)

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, tracks: list) -> dict:
        """
        Analyse a list of confirmed tracks with gamified metrics.
        """
        count   = len(tracks)
        density = self._classify(count)
        alert   = count >= self.alert_threshold
        
        if count > self.peak_count:
            self.peak_count = count

        # Gamified Metrics
        wait_time = count * 2 # 2 mins per person
        
        # Mode-specific Labels/Messages
        message = ""
        if self.mode == "canteen":
            if count < self.low_threshold:
                message = "Good time to go"
            elif count <= self.high_threshold:
                message = "Moderately busy"
            else:
                message = "Avoid now"
        elif self.mode == "shop":
            message = "Peak time usually 6 PM - 8 PM"
        elif self.mode == "event":
            if alert:
                message = "CRITICAL: OVERCROWDED"
            else:
                message = "All sections monitored"
        
        if config.ENABLE_CSV_LOGGING and self._csv_ready:
            self._log_csv(count, density, alert)

        return {
            "count":   count,
            "density": density,
            "alert":   alert,
            "peak_count": self.peak_count,
            "mode": self.mode,
            "wait_time": wait_time,
            "message": message,
            "availability": "Seats available" if count < self.high_threshold else "Almost full"
        }

    def update_mode(self, new_mode: str):
        """Dynamically update thresholds based on mode."""
        if new_mode in config.MODE_CONFIGS:
            self.mode = new_mode
            self.config = config.MODE_CONFIGS[new_mode]
            self.low_threshold   = self.config["low_threshold"]
            self.high_threshold  = self.config["high_threshold"]
            self.alert_threshold = self.config["alert_threshold"]
            self.labels          = self.config["labels"]
            print(f"[INFO] Analysis mode switched to: {new_mode.upper()}")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _classify(self, count: int) -> str:
        """Return a density label based on configured thresholds & mode labels."""
        if count < self.low_threshold:
            return self.labels[0]
        elif count <= self.high_threshold:
            return self.labels[1]
        else:
            return self.labels[2]

    def _init_csv(self, path: str) -> None:
        """Create the CSV file with headers if it does not already exist."""
        try:
            write_header = not os.path.exists(path)
            self._csv_file = open(path, "a", newline="")    # noqa: WPS515
            self._csv_writer = csv.writer(self._csv_file)
            if write_header:
                self._csv_writer.writerow(["timestamp", "count", "density", "alert"])
                self._csv_file.flush()
            self._csv_ready = True
            print(f"[INFO] CSV logging enabled → {os.path.abspath(path)}")
        except IOError as exc:
            print(f"[WARN] Could not open CSV log file: {exc}")

    def _log_csv(self, count: int, density: str, alert: bool) -> None:
        """Append one row to the CSV log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._csv_writer.writerow([timestamp, count, density, int(alert)])
        self._csv_file.flush()

    def __del__(self):
        """Close the CSV file handle gracefully."""
        if self._csv_ready:
            try:
                self._csv_file.close()
            except Exception:
                pass
