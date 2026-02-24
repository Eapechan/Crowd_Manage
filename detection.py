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
        self.person_class_id = config.PERSON_CLASS_ID

    def detect(self, frame: np.ndarray) -> list:
        """
        Run inference on a single frame.

        Parameters
        ----------
        frame : np.ndarray
            BGR image (as returned by OpenCV).

        Returns
        -------
        list of ([x, y, w, h], confidence, class_name) tuples.
            The bounding box is in (top-left-x, top-left-y, width, height) format
            because that is what deep-sort-realtime expects.
        """
        detections = []

        # Run inference (verbose=False keeps the console clean)
        results = self.model(frame, verbose=False)[0]

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])

            # Only keep "person" detections above the confidence threshold
            if cls_id != self.person_class_id or conf < self.confidence_threshold:
                continue

            # xyxy → x1, y1, x2, y2
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w = x2 - x1
            h = y2 - y1

            detections.append(([x1, y1, w, h], conf, "person"))

        return detections
