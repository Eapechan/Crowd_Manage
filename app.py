# app.py
# ─────────────────────────────────────────────────────────────────────────────
# Streamlit Dashboard for the Crowd Management System.
#
# Usage:
#   streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

import time
import threading
from collections import deque
from datetime import datetime

import cv2
import numpy as np
import streamlit as st
import pandas as pd

import config
from detection import PersonDetector
from tracking  import PersonTracker
from analysis  import CrowdAnalyzer


# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Crowd Management System",
    page_icon="👥",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS – sleek dark theme
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    body, .stApp { background-color: #0d1117; color: #c9d1d9; }
    h1, h2, h3   { color: #58a6ff; }
    .metric-box  {
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 10px;
        background: #161b22;
        border: 1px solid #30363d;
    }
    .alert-box {
        border-radius: 10px;
        padding: 16px;
        background: rgba(220,53,69,.18);
        border: 1px solid #dc3545;
        color: #ff8080;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .safe-box {
        border-radius: 10px;
        padding: 16px;
        background: rgba(40,167,69,.15);
        border: 1px solid #28a745;
        color: #5cdb5c;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .density-LOW    { color: #28a745; }
    .density-MEDIUM { color: #fd7e14; }
    .density-HIGH   { color: #dc3545; }
    [data-testid="stSidebar"] { background-color: #161b22; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session-state initialisation
# ─────────────────────────────────────────────────────────────────────────────

if "running" not in st.session_state:
    st.session_state.running = False
if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=200)   # rolling window

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar – settings
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️  Settings")

    source_type = st.radio("Input Source", ["Webcam", "Video File"])
    if source_type == "Webcam":
        cam_index = st.number_input("Camera Index", 0, 10, 0, step=1)
        video_source = int(cam_index)
    else:
        video_path = st.text_input("Video File Path", placeholder="path/to/video.mp4")
        video_source = video_path if video_path else 0

    st.divider()
    low_thresh  = st.slider("LOW  threshold",  1, 50, config.LOW_THRESHOLD)
    high_thresh = st.slider("HIGH threshold", low_thresh + 1, 100, config.HIGH_THRESHOLD)
    conf_thresh = st.slider("YOLO confidence", 0.1, 1.0, config.CONFIDENCE_THRESHOLD, 0.05)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶  Start", use_container_width=True, type="primary")
    with col2:
        stop_btn = st.button("⏹  Stop",  use_container_width=True)

    if start_btn:
        st.session_state.running = True
        st.session_state.history.clear()
    if stop_btn:
        st.session_state.running = False

# ─────────────────────────────────────────────────────────────────────────────
# Main layout
# ─────────────────────────────────────────────────────────────────────────────

st.title("👥  Crowd Management System")
st.caption("Real-time people detection, tracking & density classification")

top_col1, top_col2, top_col3 = st.columns([1, 1, 1])
with top_col1:
    count_slot   = st.empty()
with top_col2:
    density_slot = st.empty()
with top_col3:
    alert_slot   = st.empty()

st.divider()

feed_col, chart_col = st.columns([2, 1])
with feed_col:
    st.subheader("Live Feed")
    frame_slot = st.empty()
with chart_col:
    st.subheader("People Count History")
    chart_slot = st.empty()

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _placeholder_frame(msg: str = "Camera not running") -> np.ndarray:
    """Return a dark placeholder image."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (22, 27, 34)
    cv2.putText(img, msg, (60, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (88, 166, 255), 2)
    return img


def _draw_tracks_on_frame(frame, tracks, alert):
    """Draw bounding boxes and IDs on the frame (same as main.py)."""
    color = config.BOX_COLOR_ALERT if alert else config.BOX_COLOR_NORMAL
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]
        label = f"ID:{t['track_id']}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return frame


def _format_metric(label, value, color):
    return f"""
    <div class="metric-box">
        <small style="color:#8b949e">{label}</small><br/>
        <span style="font-size:2rem;font-weight:700;color:{color}">{value}</span>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

if not st.session_state.running:
    frame_slot.image(_placeholder_frame(), channels="BGR", use_column_width=True)
    count_slot.markdown(_format_metric("People Count", "–", "#58a6ff"),  unsafe_allow_html=True)
    density_slot.markdown(_format_metric("Density",     "–", "#8b949e"), unsafe_allow_html=True)
    alert_slot.markdown('<div class="safe-box">✅  System idle</div>',  unsafe_allow_html=True)

else:
    # ── Lazy-init heavy components ────────────────────────────────────────────
    try:
        config.CONFIDENCE_THRESHOLD = conf_thresh
        config.LOW_THRESHOLD  = low_thresh
        config.HIGH_THRESHOLD = high_thresh
        config.ALERT_THRESHOLD = high_thresh

        detector = PersonDetector()
        tracker  = PersonTracker()
        analyzer = CrowdAnalyzer(
            low_threshold=low_thresh,
            high_threshold=high_thresh,
            alert_threshold=high_thresh,
        )
    except Exception as e:
        st.error(f"Initialisation error: {e}")
        st.stop()

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        st.error(f"❌  Cannot open video source: {video_source}")
        st.stop()

    density_colors = {"LOW": "#28a745", "MEDIUM": "#fd7e14", "HIGH": "#dc3545"}

    while st.session_state.running:
        ret, frame = cap.read()
        if not ret:
            st.warning("⚠️  End of stream or camera disconnected.")
            break

        # Pipeline
        dets   = detector.detect(frame)
        tracks = tracker.update(dets, frame)
        result = analyzer.analyze(tracks)

        count   = result["count"]
        density = result["density"]
        alert   = result["alert"]

        # Record history
        st.session_state.history.append({"time": datetime.now(), "count": count})

        # Annotate frame
        frame = _draw_tracks_on_frame(frame, tracks, alert)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ── Update UI slots ───────────────────────────────────────────────────
        frame_slot.image(rgb, channels="RGB", use_column_width=True)

        count_slot.markdown(
            _format_metric("People Count", count, "#58a6ff"),
            unsafe_allow_html=True,
        )
        density_slot.markdown(
            _format_metric("Density", density, density_colors[density]),
            unsafe_allow_html=True,
        )

        if alert:
            alert_slot.markdown(
                '<div class="alert-box">🚨  ALERT: Overcrowding Detected!</div>',
                unsafe_allow_html=True,
            )
        else:
            alert_slot.markdown(
                '<div class="safe-box">✅  Crowd Level Normal</div>',
                unsafe_allow_html=True,
            )

        # Chart
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            df = df.set_index("time")
            chart_slot.line_chart(df["count"], height=300)

        time.sleep(0.03)   # ~30 fps cap

    cap.release()
