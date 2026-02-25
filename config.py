# config.py
# ─────────────────────────────────────────────────────────────────────────────
# Central configuration for the Crowd Management System.
# Edit these values to tune detection, tracking, and alert behaviour.
# ─────────────────────────────────────────────────────────────────────────────

# ── YOLOv8 model ─────────────────────────────────────────────────────────────
MODEL_NAME = "yolov8s.pt"          # Small model (best for accuracy/speed balance)
CONFIDENCE_THRESHOLD = 0.6         # Main filter (strict)
IOU_THRESHOLD = 0.45               # NMS threshold
PERSON_CLASS_ID = 0                # COCO "person"

# ── Video source & Performance ────────────────────────────────────────────────
# 0 = default webcam  |  "path/to/video.mp4" = video file
VIDEO_SOURCE = 0
FRAME_SKIP = 2                     # Process every 2nd frame
PROCESS_SIZE = (640, 480)          # Resize frame for detection

# ── Multi-Mode Settings ────────────────────────────────────────────────────────
# Modes: "canteen", "shop", "event"
CURRENT_MODE = "canteen"

MODE_CONFIGS = {
    "canteen": {
        "low_threshold": 10,
        "high_threshold": 30,
        "alert_threshold": 30,
        "labels": ["FREE", "MODERATE", "CROWDED"]
    },
    "shop": {
        "low_threshold": 5,
        "high_threshold": 15,
        "alert_threshold": 20,
        "labels": ["LOW", "MEDIUM", "HIGH"]
    },
    "event": {
        "low_threshold": 50,
        "high_threshold": 150,
        "alert_threshold": 200,
        "labels": ["NORMAL", "BUSY", "OVERCROWDED"]
    }
}

# ── Dynamic Filtering ────────────────────────────────────────────────────────
AREA_RATIO = 0.002                 # Area threshold as % of total frame area
MIN_TRACK_AGE = 3                  # Age threshold (hits) to remove flickering

# ── DeepSORT settings ─────────────────────────────────────────────────────────
MAX_AGE = 30                       # Keep lost track for 30 frames
N_INIT = 3                         # Confirmed after 3 detections (matches track_age)
MAX_IOU_DISTANCE = 0.7             # IoU matching threshold

# ── Display / OpenCV (Legacy fallback) ────────────────────────────────────────
WINDOW_TITLE = "Crowd Management System (Optimized)"
BOX_COLOR_NORMAL  = (0, 200, 0)    # green
BOX_COLOR_ALERT   = (0, 0, 255)    # red
TEXT_COLOR        = (255, 255, 255)
FONT_SCALE        = 0.55
BOX_THICKNESS     = 2

# ── CSV logging (optional) ────────────────────────────────────────────────────
ENABLE_CSV_LOGGING = True
CSV_FILE_PATH = "crowd_log.csv"
