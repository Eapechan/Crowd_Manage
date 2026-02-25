# detection.py
# ─────────────────────────────────────────────────────────────────────────────
# PersonDetector – wraps YOLOv8 and filters results to the "person" class only.
# ─────────────────────────────────────────────────────────────────────────────

from ultralytics import YOLO
import numpy as np
import config


class PersonDetector:
    """
    Loads a YOLOv8 model and detects people in a given frame.

    Returns detections in the format expected by DeepSORT:
        [ ([x1, y1, w, h], confidence, class_name), ... ]
    """

    def __init__(self):
        print(f"[INFO] Loading YOLOv8 model: {config.MODEL_NAME}")
        self.model = YOLO(config.MODEL_NAME)
        self.confidence_threshold = config.CONFIDENCE_THRESHOLD
        self.iou_threshold = config.IOU_THRESHOLD
        self.person_class_id = getattr(config, 'PERSON_CLASS_ID', 0)
        self.area_ratio = getattr(config, 'AREA_RATIO', 0.002)

    def detect(self, frame: np.ndarray) -> list:
        """
        Run inference on a single frame with dynamic area filtering.
        """
        detections = []
        h, w = frame.shape[:2]
        frame_area = h * w

        # Run inference with built-in filters
        results = self.model(
            frame,
            classes=[self.person_class_id],
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False
        )[0]

        num_raw = len(results.boxes)
        for box in results.boxes:
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            bw = x2 - x1
            bh = y2 - y1
            area = bw * bh

            # Dynamic Area Filter: Removes small noise (books, hands, etc.)
            if area < self.area_ratio * frame_area:
                continue

            # Add to list for DeepSORT
            detections.append(([x1, y1, bw, bh], conf, "person"))

        if num_raw > 0:
            print(f"[DEBUG] YOLO: {num_raw} raw, {len(detections)} filtered (Area > {self.area_ratio*100}%)")

        return detections
