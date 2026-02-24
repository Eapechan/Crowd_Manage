# analysis.py
# ─────────────────────────────────────────────────────────────────────────────
# CrowdAnalyzer – counts people, classifies density, and raises alerts.
# ─────────────────────────────────────────────────────────────────────────────

import csv
import os
from datetime import datetime
import config


# ── Density labels ────────────────────────────────────────────────────────────
DENSITY_LOW    = "LOW"
DENSITY_MEDIUM = "MEDIUM"
DENSITY_HIGH   = "HIGH"

# ── Colour tiers (for external display components) ────────────────────────────
DENSITY_COLOR = {
    DENSITY_LOW:    "#28a745",   # green
    DENSITY_MEDIUM: "#fd7e14",   # orange
    DENSITY_HIGH:   "#dc3545",   # red
}


class CrowdAnalyzer:
    """
    Stateless helper that converts a list of confirmed tracks into:
        - person count
        - density label  (LOW | MEDIUM | HIGH)
        - alert flag     (True when count > ALERT_THRESHOLD)

    Optionally logs each reading to a CSV file.
    """

    def __init__(
        self,
        low_threshold:  int = config.LOW_THRESHOLD,
        high_threshold: int = config.HIGH_THRESHOLD,
        alert_threshold: int = config.ALERT_THRESHOLD,
    ):
        self.low_threshold   = low_threshold
        self.high_threshold  = high_threshold
        self.alert_threshold = alert_threshold

        # CSV logging setup
        self._csv_ready = False
        if config.ENABLE_CSV_LOGGING:
            self._init_csv(config.CSV_FILE_PATH)

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, tracks: list) -> dict:
        """
        Analyse a list of confirmed tracks.

        Parameters
        ----------
        tracks : list
            Output of PersonTracker.update().

        Returns
        -------
        dict with keys:
            count    – int
            density  – str  (LOW | MEDIUM | HIGH)
            alert    – bool
        """
        count   = len(tracks)
        density = self._classify(count)
        alert   = count > self.alert_threshold

        if config.ENABLE_CSV_LOGGING and self._csv_ready:
            self._log_csv(count, density, alert)

        return {
            "count":   count,
            "density": density,
            "alert":   alert,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _classify(self, count: int) -> str:
        """Return a density label based on configured thresholds."""
        if count < self.low_threshold:
            return DENSITY_LOW
        elif count <= self.high_threshold:
            return DENSITY_MEDIUM
        else:
            return DENSITY_HIGH

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
