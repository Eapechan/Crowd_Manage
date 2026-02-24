# app.py
# ─────────────────────────────────────────────────────────────────────────────
# Streamlit Dashboard — Crowd Management System
#
# Architecture:
#   • Each script rerun = one video frame processed
#   • st.rerun() drives the next frame (no blocking while-loop)
#   • Heavy objects (detector / tracker / cap) live in session_state
#   • Chart uses integer frame index — avoids Vega-Lite datetime crash
#
# Usage:  streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

import time

import cv2
import numpy as np
import streamlit as st
import pandas as pd

import config
from detection import PersonDetector
from tracking  import PersonTracker
from analysis  import CrowdAnalyzer

# ── Page config (must be first) ───────────────────────────────────────────────
st.set_page_config(
    page_title="Crowd Management System",
    page_icon="👥",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
body, .stApp           { background:#0d1117; color:#c9d1d9; }
h1, h2, h3             { color:#58a6ff; }
.metric-box {
    border-radius:12px; padding:18px 22px; margin-bottom:10px;
    background:#161b22; border:1px solid #30363d;
}
.alert-box {
    border-radius:10px; padding:16px;
    background:rgba(220,53,69,.18); border:1px solid #dc3545;
    color:#ff8080; font-size:1.05rem; font-weight:600;
}
.safe-box {
    border-radius:10px; padding:16px;
    background:rgba(40,167,69,.15); border:1px solid #28a745;
    color:#5cdb5c; font-size:1.05rem; font-weight:600;
}
[data-testid="stSidebar"] { background:#161b22; }
</style>
""", unsafe_allow_html=True)

# ── Session-state defaults ────────────────────────────────────────────────────
_DEFAULTS = dict(
    running=False, frame_idx=0,
    count_history=[],          # list of ints — safe for Vega-Lite
    last_count=0, last_density="LOW", last_alert=False,
    detector=None, tracker=None, analyzer=None, cap=None,
)
for k, v in _DEFAULTS.items():
    st.session_state.setdefault(k, v)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    locked = st.session_state.running
    src_type = st.radio("Input Source", ["Webcam", "Video File"], disabled=locked)
    if src_type == "Webcam":
        cam_idx = st.number_input("Camera Index", 0, 10, 0, step=1, disabled=locked)
        video_source: int | str = int(cam_idx)
    else:
        vpath = st.text_input("Video File Path", placeholder="path/to/video.mp4",
                               disabled=locked)
        video_source = vpath or 0

    st.divider()
    low_thr  = st.slider("LOW  threshold (<)",  1, 50,  config.LOW_THRESHOLD,  disabled=locked)
    high_thr = st.slider("HIGH threshold (>)", low_thr+1, 100, config.HIGH_THRESHOLD, disabled=locked)
    conf_thr = st.slider("YOLO confidence",    0.1, 1.0, config.CONFIDENCE_THRESHOLD, 0.05, disabled=locked)

    st.divider()
    c1, c2 = st.columns(2)
    start_btn = c1.button("▶ Start", use_container_width=True,
                           type="primary", disabled=locked)
    stop_btn  = c2.button("⏹ Stop",  use_container_width=True,
                           disabled=not locked)

# ── Start handler ─────────────────────────────────────────────────────────────
if start_btn and not st.session_state.running:
    config.CONFIDENCE_THRESHOLD = conf_thr
    config.LOW_THRESHOLD  = low_thr
    config.HIGH_THRESHOLD = high_thr
    config.ALERT_THRESHOLD = high_thr
    try:
        st.session_state.detector = PersonDetector()
        st.session_state.tracker  = PersonTracker()
        st.session_state.analyzer = CrowdAnalyzer(
            low_threshold=low_thr,
            high_threshold=high_thr,
            alert_threshold=high_thr,
        )
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            st.error(f"❌ Cannot open source: {video_source}")
        else:
            st.session_state.cap = cap
            st.session_state.count_history.clear()
            st.session_state.frame_idx = 0
            st.session_state.running = True
    except Exception as exc:
        st.error(f"Init error: {exc}")

# ── Stop handler ──────────────────────────────────────────────────────────────
if stop_btn and st.session_state.running:
    st.session_state.running = False
    if st.session_state.cap:
        st.session_state.cap.release()
        st.session_state.cap = None

# ── Layout ────────────────────────────────────────────────────────────────────
st.title("👥 Crowd Management System")
st.caption("Real-time detection · tracking · density classification")

col_a, col_b, col_c = st.columns(3)
count_slot   = col_a.empty()
density_slot = col_b.empty()
alert_slot   = col_c.empty()

st.divider()
feed_col, chart_col = st.columns([2, 1])
frame_slot = feed_col.empty()
chart_slot = chart_col.empty()

# ── Helpers ───────────────────────────────────────────────────────────────────
_DCOL = {"LOW": "#28a745", "MEDIUM": "#fd7e14", "HIGH": "#dc3545"}

def render_metrics(count, density, alert):
    count_slot.markdown(f"""
    <div class="metric-box">
      <small style="color:#8b949e">👥 People Count</small><br/>
      <span style="font-size:2.4rem;font-weight:800;color:#58a6ff">{count}</span>
    </div>""", unsafe_allow_html=True)

    density_slot.markdown(f"""
    <div class="metric-box">
      <small style="color:#8b949e">📊 Crowd Density</small><br/>
      <span style="font-size:2.4rem;font-weight:800;color:{_DCOL[density]}">{density}</span>
    </div>""", unsafe_allow_html=True)

    alert_slot.markdown(
        '<div class="alert-box">🚨 ALERT: Overcrowding!</div>'
        if alert else
        '<div class="safe-box">✅ Crowd Level Normal</div>',
        unsafe_allow_html=True,
    )

def render_chart(history: list):
    """Render count history using a plain integer x-axis (no datetime)."""
    if len(history) < 2:
        chart_slot.info("Collecting data…")
        return
    # Keep last 120 points so the chart stays readable
    tail = history[-120:]
    df = pd.DataFrame({"Count": tail})   # integer index 0..N — no datetime
    chart_col.subheader("📈 Count History")
    chart_slot.line_chart(df, height=280)

def placeholder_frame(msg="Camera not running"):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (22, 27, 34)
    cv2.putText(img, msg, (40, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (88, 166, 255), 2)
    return img

def annotate(frame, tracks, alert):
    color = config.BOX_COLOR_ALERT if alert else config.BOX_COLOR_NORMAL
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]
        lbl = f"ID:{t['track_id']}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1-th-6), (x1+tw+4, y1), color, -1)
        cv2.putText(frame, lbl, (x1+2, y1-4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1, cv2.LINE_AA)
    return frame

# ── Idle state ────────────────────────────────────────────────────────────────
if not st.session_state.running:
    feed_col.subheader("📷 Live Feed")
    frame_slot.image(placeholder_frame(), channels="BGR",
                     use_container_width=True)
    render_metrics(
        st.session_state.last_count,
        st.session_state.last_density,
        st.session_state.last_alert,
    )
    render_chart(st.session_state.count_history)
    st.stop()

# ── LIVE: process one frame then rerun ────────────────────────────────────────
cap = st.session_state.cap
ret, frame = cap.read()

if not ret:
    st.warning("⚠️ Stream ended or camera disconnected.")
    st.session_state.running = False
    cap.release()
    st.session_state.cap = None
    st.stop()

# Pipeline
dets   = st.session_state.detector.detect(frame)
tracks = st.session_state.tracker.update(dets, frame)
result = st.session_state.analyzer.analyze(tracks)

count   = result["count"]
density = result["density"]
alert   = result["alert"]

# Persist state
st.session_state.last_count   = count
st.session_state.last_density = density
st.session_state.last_alert   = alert
st.session_state.count_history.append(count)
st.session_state.frame_idx += 1

# Draw
frame = annotate(frame, tracks, alert)
rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

feed_col.subheader("📷 Live Feed")
frame_slot.image(rgb, channels="RGB", use_container_width=True)
render_metrics(count, density, alert)

# Only redraw chart every 5 frames to reduce CPU load
if st.session_state.frame_idx % 5 == 0:
    render_chart(st.session_state.count_history)

# Small sleep to keep CPU usage sane, then trigger next frame
time.sleep(0.04)
st.rerun()
