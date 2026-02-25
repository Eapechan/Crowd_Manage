# Crowd Management System — README
# =============================================================================

# ──────────────────────────────────────────────────────────────────────────────
# PROJECT OVERVIEW
# ──────────────────────────────────────────────────────────────────────────────
"""
A real-time Crowd Management System built with:
  • YOLOv8   – person detection
  • DeepSORT – multi-object tracking with unique IDs
  • OpenCV   – real-time video display
  • Streamlit – web dashboard

crowd_management/
├── config.py      ← thresholds, paths, display colours
├── detection.py   ← YOLOv8 wrapper (persons only)
├── tracking.py    ← DeepSORT tracker
├── analysis.py    ← density classification + CSV logging
├── main.py        ← OpenCV real-time window
└── app.py         ← Streamlit dashboard
"""
