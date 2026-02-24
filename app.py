# app.py
# ─────────────────────────────────────────────────────────────────────────────
# Streamlit Dashboard for the Crowd Management System.
#
# KEY DESIGN: Streamlit is REACTIVE – it re-runs the whole script on each
# interaction.  We therefore:
#   1. Store heavy objects (detector, tracker, cap) in st.session_state so
#      they are created only once.
#   2. Process exactly ONE frame per script run.
#   3. Call st.rerun() at the end to trigger the next frame automatically.
#
# Usage:  streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

import time
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
# Page config  (MUST be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crowd Management System",
    page_icon="👥",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# Dark theme CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
body, .stApp           { background-color: #0d1117; color: #c9d1d9; }
h1, h2, h3             { color: #58a6ff; }
.metric-box {
    border-radius: 12px; padding: 18px 22px; margin-bottom: 10px;
    background: #161b22; border: 1px solid #30363d;
}
.alert-box {
    border-radius: 10px; padding: 16px;
    background: rgba(220,53,69,.18); border: 1px solid #dc3545;
    color: #ff8080; font-size: 1.05rem; font-weight: 600;
}
.safe-box {
    border-radius: 10px; padding: 16px;
    background: rgba(40,167,69,.15); border: 1px solid #28a745;
    color: #5cdb5c; font-size: 1.05rem; font-weight: 600;
}
[data-testid="stSidebar"] { background-color: #161b22; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session-state defaults  (set only once)
# ─────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "running":    False,
        "history":    deque(maxlen=200),
        "last_count": 0,
        "last_density": "LOW",
        "last_alert": False,
        # heavy objects — created on demand
        "detector":   None,
        "tracker":    None,
        "analyzer":   None,
        "cap":        None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar – settings & controls
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️  Settings")

    source_type = st.radio("Input Source", ["Webcam", "Video File"],
                           disabled=st.session_state.running)
    if source_type == "Webcam":
        cam_index = st.number_input("Camera Index", 0, 10, 0, step=1,
                                    disabled=st.session_state.running)
        video_source = int(cam_index)
    else:
        video_path = st.text_input("Video File Path",
                                   placeholder="path/to/video.mp4",
                                   disabled=st.session_state.running)
        video_source = video_path if video_path else 0

    st.divider()
    low_thresh  = st.slider("LOW  threshold (<)",  1, 50,
                             config.LOW_THRESHOLD,
                             disabled=st.session_state.running)
    high_thresh = st.slider("HIGH threshold (>)",
                             low_thresh + 1, 100,
                             config.HIGH_THRESHOLD,
                             disabled=st.session_state.running)
    conf_thresh = st.slider("YOLO confidence", 0.1, 1.0,
                             config.CONFIDENCE_THRESHOLD, 0.05,
                             disabled=st.session_state.running)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶  Start", use_container_width=True,
                               type="primary",
                               disabled=st.session_state.running)
    with col2:
        stop_btn  = st.button("⏹  Stop",  use_container_width=True,
                               disabled=not st.session_state.running)

# ── Handle Start ──────────────────────────────────────────────────────────────
if start_btn and not st.session_state.running:
    # Update config with sidebar values
    config.CONFIDENCE_THRESHOLD = conf_thresh
    config.LOW_THRESHOLD        = low_thresh
    config.HIGH_THRESHOLD       = high_thresh
    config.ALERT_THRESHOLD      = high_thresh

    # Initialise heavy objects once
    try:
        st.session_state.detector = PersonDetector()
        st.session_state.tracker  = PersonTracker()
        st.session_state.analyzer = CrowdAnalyzer(
            low_threshold=low_thresh,
            high_threshold=high_thresh,
            alert_threshold=high_thresh,
        )
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            st.error(f"❌  Cannot open video source: {video_source}")
        else:
            st.session_state.cap = cap
            st.session_state.history.clear()
            st.session_state.running = True
    except Exception as e:
        st.error(f"Initialisation error: {e}")

# ── Handle Stop ───────────────────────────────────────────────────────────────
if stop_btn and st.session_state.running:
    st.session_state.running = False
    if st.session_state.cap is not None:
        st.session_state.cap.release()
        st.session_state.cap = None

# ─────────────────────────────────────────────────────────────────────────────
# Main layout – slots
# ─────────────────────────────────────────────────────────────────────────────
st.title("👥  Crowd Management System")
st.caption("Real-time people detection · tracking · density classification")

m1, m2, m3 = st.columns(3)
with m1:
    count_slot   = st.empty()
with m2:
    density_slot = st.empty()
with m3:
    alert_slot   = st.empty()

st.divider()

feed_col, chart_col = st.columns([2, 1])
with feed_col:
    st.subheader("📷 Live Feed")
    frame_slot = st.empty()
with chart_col:
    st.subheader("📈 Count History")
    chart_slot = st.empty()

# ─────────────────────────────────────────────────────────────────────────────
# Helper: render the metric cards
# ─────────────────────────────────────────────────────────────────────────────
DENSITY_COLORS = {"LOW": "#28a745", "MEDIUM": "#fd7e14", "HIGH": "#dc3545"}

def _render_metrics(count, density, alert):
    count_slot.markdown(f"""
    <div class="metric-box">
      <small style="color:#8b949e">👥 People Count</small><br/>
      <span style="font-size:2.4rem;font-weight:800;color:#58a6ff">{count}</span>
    </div>""", unsafe_allow_html=True)

    density_slot.markdown(f"""
    <div class="metric-box">
      <small style="color:#8b949e">📊 Crowd Density</small><br/>
      <span style="font-size:2.4rem;font-weight:800;color:{DENSITY_COLORS[density]}">{density}</span>
    </div>""", unsafe_allow_html=True)

    if alert:
        alert_slot.markdown(
            '<div class="alert-box">🚨 ALERT: Overcrowding Detected!</div>',
            unsafe_allow_html=True)
    else:
        alert_slot.markdown(
            '<div class="safe-box">✅ Crowd Level Normal</div>',
            unsafe_allow_html=True)

def _placeholder_frame(msg="Camera not running"):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (22, 27, 34)
    cv2.putText(img, msg, (40, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (88, 166, 255), 2)
    return img

def _annotate(frame, tracks, alert):
    color = config.BOX_COLOR_ALERT if alert else config.BOX_COLOR_NORMAL
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]
        label = f"ID:{t['track_id']}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1, cv2.LINE_AA)
    # HUD bar
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 50), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    return frame

# ─────────────────────────────────────────────────────────────────────────────
# Idle state
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.running:
    frame_slot.image(_placeholder_frame(), channels="BGR",
                     use_container_width=True)
    _render_metrics(
        st.session_state.last_count,
        st.session_state.last_density,
        st.session_state.last_alert,
    )
    if st.session_state.history:
        df = pd.DataFrame(list(st.session_state.history)).set_index("time")
        chart_slot.line_chart(df["count"], height=300)
    st.stop()   # don't proceed further

# ─────────────────────────────────────────────────────────────────────────────
# RUNNING — process ONE frame, then st.rerun() for the next
# ─────────────────────────────────────────────────────────────────────────────
cap = st.session_state.cap
ret, frame = cap.read()

if not ret:
    st.warning("⚠️  End of stream or camera disconnected. Press Stop.")
    st.session_state.running = False
    if cap:
        cap.release()
        st.session_state.cap = None
    st.stop()

# Pipeline
detector = st.session_state.detector
tracker  = st.session_state.tracker
analyzer = st.session_state.analyzer

dets   = detector.detect(frame)
tracks = tracker.update(dets, frame)
result = analyzer.analyze(tracks)

count   = result["count"]
density = result["density"]
alert   = result["alert"]

# Save for idle display
st.session_state.last_count   = count
st.session_state.last_density = density
st.session_state.last_alert   = alert
st.session_state.history.append({"time": datetime.now(), "count": count})

# Annotate and display frame
frame = _annotate(frame, tracks, alert)
rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
frame_slot.image(rgb, channels="RGB", use_container_width=True)

# Update metric cards
_render_metrics(count, density, alert)

# Update chart
if st.session_state.history:
    df = pd.DataFrame(list(st.session_state.history)).set_index("time")
    chart_slot.line_chart(df["count"], height=300)

# Trigger next frame – this is the key: each rerun = one frame
time.sleep(0.03)   # ~30 fps limit
st.rerun()
