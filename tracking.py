# tracking.py
# ─────────────────────────────────────────────────────────────────────────────
# PersonTracker – integrates deep-sort-realtime to assign unique IDs.
# ─────────────────────────────────────────────────────────────────────────────

from deep_sort_realtime.deepsort_tracker import DeepSort
import numpy as np
import config


class PersonTracker:
    """
    Wraps DeepSORT and converts raw YOLO detections into confirmed tracks.

    Each confirmed track carries:
        track_id  – unique integer ID (persistent across frames)
        bbox      – (x1, y1, x2, y2) bounding box in pixel coordinates
    """

    def __init__(self):
        print("[INFO] Initialising DeepSORT tracker …")
        self.tracker = DeepSort(
            max_age=config.MAX_AGE,
            n_init=config.N_INIT,
            max_iou_distance=config.MAX_IOU_DISTANCE,
            # embedder_gpu=False keeps inference on CPU
            embedder_gpu=False,
        )

    def update(self, detections: list, frame: np.ndarray) -> list:
        """
        Feed new detections into the tracker and return only stable, confirmed tracks.
        """
        raw_tracks = self.tracker.update_tracks(detections, frame=frame)

        confirmed = []
        for track in raw_tracks:
            # 1. Only keep tracks confirmed by DeepSORT
            if not track.is_confirmed():
                continue
            
            # 2. Track Stability: Minimum hits (MIN_TRACK_AGE)
            # This ensures that a person must be detected for N frames before being counted.
            if track.hits < config.MIN_TRACK_AGE:
                continue

            # 3. Ensure track is currently visible
            if track.time_since_update > 1:
                continue

            track_id = track.track_id
            ltrb     = track.to_ltrb()          # (left, top, right, bottom)
            x1, y1, x2, y2 = map(int, ltrb)

            confirmed.append({
                "track_id": track_id,
                "bbox":     (x1, y1, x2, y2),
            })

        return confirmed
