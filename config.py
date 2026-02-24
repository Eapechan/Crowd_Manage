# config.py
# ─────────────────────────────────────────────────────────────────────────────
# Central configuration for the Crowd Management System.
# Edit these values to tune detection, tracking, and alert behaviour.
# ─────────────────────────────────────────────────────────────────────────────

# ── YOLOv8 model ─────────────────────────────────────────────────────────────
MODEL_NAME = "yolov8n.pt"          # nano model – fastest on CPU; swap for yolov8s.pt for better accuracy
CONFIDENCE_THRESHOLD = 0.4         # minimum detection confidence (0‑1)
PERSON_CLASS_ID = 0                # COCO class index for "person"

# ── Video source ──────────────────────────────────────────────────────────────
# 0 = default webcam  |  "path/to/video.mp4" = video file
VIDEO_SOURCE = 0

# ── DeepSORT settings ─────────────────────────────────────────────────────────
MAX_AGE = 30                       # frames to keep a lost track alive
N_INIT = 3                         # min detections before confirming a track
MAX_IOU_DISTANCE = 0.7             # max IoU distance for matching

# ── Crowd density thresholds ─────────────────────────────────────────────────
LOW_THRESHOLD = 10                 # below this → LOW density
HIGH_THRESHOLD = 25                # above this → HIGH density  (between LOW and HIGH → MEDIUM)

# ── Alert ─────────────────────────────────────────────────────────────────────
ALERT_THRESHOLD = HIGH_THRESHOLD   # count that triggers an overcrowding alert

# ── Display / OpenCV ─────────────────────────────────────────────────────────
WINDOW_TITLE = "Crowd Management System"
BOX_COLOR_NORMAL  = (0, 200, 0)    # green  – normal crowd
BOX_COLOR_ALERT   = (0, 0, 255)    # red    – crowd alert
TEXT_COLOR        = (255, 255, 255)
FONT_SCALE        = 0.55
BOX_THICKNESS     = 2

# ── CSV logging (optional) ────────────────────────────────────────────────────
ENABLE_CSV_LOGGING = True
CSV_FILE_PATH = "crowd_log.csv"
