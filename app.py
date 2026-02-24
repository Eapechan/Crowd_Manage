# app.py
# ─────────────────────────────────────────────────────────────────────────────
# Premium AI Dashboard — Crowd Management System
# Design: Tesla / Security-monitoring dark glassmorphism
#
# Improvements in this version
# ─────────────────────────────
# • Plotly charts instead of st.line_chart  →  fixes Vega-Lite "Infinite extent"
# • Base64 <img> for video feed             →  fixes MediaFileStorageError
# • FPS counter & peak count cards
# • Full glassmorphism metric cards
# • Futuristic header with animated LIVE badge
# • Two charts: real-time line + density bar
# ─────────────────────────────────────────────────────────────────────────────

import base64
import time

import cv2
import numpy as np
import streamlit as st
import plotly.graph_objects as go

import config
from detection import PersonDetector
from tracking  import PersonTracker
from analysis  import CrowdAnalyzer

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crowd AI Monitor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Full CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset ── */
html, body, .stApp {
    background: #0D1117 !important;
    color: #E6EDF3 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid #21262D;
}

/* ── Header ── */
.cms-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
    border: 1px solid #30363D;
    border-radius: 16px;
    padding: 18px 28px;
    margin-bottom: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
.cms-title {
    font-size: 1.55rem;
    font-weight: 800;
    background: linear-gradient(90deg, #58A6FF, #A5D6FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}
.cms-subtitle { font-size:.78rem; color:#8B949E; margin-top:2px; }
.live-badge {
    display:flex; align-items:center; gap:8px;
    background:rgba(46,204,113,.12);
    border:1px solid rgba(46,204,113,.35);
    border-radius:50px;
    padding:6px 16px;
    font-size:.8rem; font-weight:600; color:#2ECC71;
}
.offline-badge {
    display:flex; align-items:center; gap:8px;
    background:rgba(139,148,158,.1);
    border:1px solid rgba(139,148,158,.3);
    border-radius:50px;
    padding:6px 16px;
    font-size:.8rem; font-weight:600; color:#8B949E;
}
.dot { width:8px;height:8px;border-radius:50%;background:#2ECC71;
       animation:pulse 1.5s ease-in-out infinite; }
.dot-off { width:8px;height:8px;border-radius:50%;background:#8B949E; }
@keyframes pulse {
    0%,100%{box-shadow:0 0 0 0 rgba(46,204,113,.6);}
    50%{box-shadow:0 0 0 6px rgba(46,204,113,0);}
}

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, rgba(22,27,34,0.95) 0%, rgba(30,37,48,0.95) 100%);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid #30363D;
    border-radius: 16px;
    padding: 20px 22px 18px;
    margin-bottom: 4px;
    transition: transform .2s, box-shadow .2s;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content:'';
    position:absolute; top:0; left:0; right:0; height:2px;
}
.card-blue::before   { background: linear-gradient(90deg,#58A6FF,#1F6FEB); }
.card-green::before  { background: linear-gradient(90deg,#2ECC71,#27AE60); }
.card-orange::before { background: linear-gradient(90deg,#F39C12,#E67E22); }
.card-red::before    { background: linear-gradient(90deg,#E74C3C,#C0392B); }
.card-purple::before { background: linear-gradient(90deg,#9B59B6,#8E44AD); }
.metric-icon { font-size:1.6rem; margin-bottom:6px; }
.metric-value { font-size:2.4rem; font-weight:800; line-height:1; margin:4px 0 2px; }
.metric-label { font-size:.72rem; color:#8B949E; font-weight:500;
                text-transform:uppercase; letter-spacing:0.8px; }
.metric-sub   { font-size:.68rem; color:#58A6FF; margin-top:4px; }

/* ── Video ── */
.video-container {
    background:#161B22;
    border: 1px solid #30363D;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.video-header {
    display:flex; align-items:center; justify-content:space-between;
    padding:12px 16px;
    border-bottom:1px solid #21262D;
    font-size:.82rem; font-weight:600; color:#8B949E;
}
.live-dot { display:inline-block;width:6px;height:6px;border-radius:50%;
             background:#E74C3C; margin-right:6px;
             animation:pulse-red 1s ease-in-out infinite; }
@keyframes pulse-red{0%,100%{opacity:1;}50%{opacity:.4;}}
.video-body img { width:100%; display:block; }

/* ── Alert ── */
.alert-critical {
    background: linear-gradient(135deg, rgba(231,76,60,.15), rgba(192,57,43,.1));
    border: 1px solid rgba(231,76,60,.5);
    border-left: 4px solid #E74C3C;
    border-radius: 12px;
    padding: 14px 18px;
    color: #FF6B6B;
    font-size: .95rem; font-weight: 600;
    display:flex; align-items:center; gap:12px;
    animation: flash .8s ease-in-out infinite alternate;
}
@keyframes flash{from{border-color:rgba(231,76,60,.5);}to{border-color:#E74C3C;}}
.alert-safe {
    background: linear-gradient(135deg, rgba(46,204,113,.1), rgba(39,174,96,.08));
    border: 1px solid rgba(46,204,113,.35);
    border-left: 4px solid #2ECC71;
    border-radius: 12px;
    padding: 14px 18px;
    color: #2ECC71;
    font-size: .95rem; font-weight: 600;
    display:flex; align-items:center; gap:12px;
}

/* ── Sidebar ── */
.sidebar-title {
    font-size:.7rem; font-weight:700; color:#58A6FF;
    text-transform:uppercase; letter-spacing:1.2px;
    margin-bottom:8px;
}
.stSlider > div > div { background:#1C2128 !important; }
.stButton > button {
    border-radius:10px !important;
    font-weight:600 !important;
    font-size:.88rem !important;
    transition:all .2s !important;
}

/* ── Chart container ── */
.chart-card {
    background:#161B22;
    border:1px solid #30363D;
    border-radius:16px;
    padding:4px;
    box-shadow:0 4px 20px rgba(0,0,0,0.3);
    margin-bottom:12px;
}

/* ── Section label ── */
.section-label {
    font-size:.7rem; font-weight:700; color:#8B949E;
    text-transform:uppercase; letter-spacing:1px;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ── Session-state defaults ────────────────────────────────────────────────────
_DEFAULTS = dict(
    running=False, frame_idx=0,
    count_history=[],
    density_tally={"LOW": 0, "MEDIUM": 0, "HIGH": 0},
    last_count=0, last_density="LOW", last_alert=False,
    peak_count=0,
    fps_times=[],          # rolling list of frame timestamps for FPS calc
    detector=None, tracker=None, analyzer=None, cap=None,
)
for k, v in _DEFAULTS.items():
    st.session_state.setdefault(k, v)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 AI Crowd Monitor")
    st.divider()

    locked = st.session_state.running

    st.markdown('<div class="sidebar-title">📹 Video Source</div>', unsafe_allow_html=True)
    src_type = st.radio("", ["Webcam", "Video File"], disabled=locked,
                        label_visibility="collapsed")
    if src_type == "Webcam":
        cam_idx = st.number_input("Camera Index", 0, 10, 0, step=1, disabled=locked)
        video_source: int | str = int(cam_idx)
    else:
        vpath = st.text_input("File Path", placeholder="path/to/video.mp4", disabled=locked)
        video_source = vpath or 0

    st.divider()
    st.markdown('<div class="sidebar-title">⚙️ Detection Settings</div>', unsafe_allow_html=True)
    low_thr  = st.slider("LOW Threshold (<)",  1,  50, config.LOW_THRESHOLD,  disabled=locked)
    high_thr = st.slider("HIGH Threshold (>)", low_thr+1, 100, config.HIGH_THRESHOLD, disabled=locked)
    conf_thr = st.slider("YOLO Confidence",    0.1, 1.0, config.CONFIDENCE_THRESHOLD,
                          0.05, disabled=locked)

    st.divider()
    c1, c2 = st.columns(2)
    start_btn = c1.button("▶ Start", use_container_width=True,
                           type="primary", disabled=locked)
    stop_btn  = c2.button("⏹ Stop",  use_container_width=True, disabled=not locked)

# ── Start / Stop handlers ─────────────────────────────────────────────────────
if start_btn and not st.session_state.running:
    config.CONFIDENCE_THRESHOLD = conf_thr
    config.LOW_THRESHOLD        = low_thr
    config.HIGH_THRESHOLD       = high_thr
    config.ALERT_THRESHOLD      = high_thr
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
            st.error(f"❌ Cannot open: {video_source}")
        else:
            st.session_state.cap           = cap
            st.session_state.count_history = []
            st.session_state.density_tally = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
            st.session_state.peak_count    = 0
            st.session_state.frame_idx     = 0
            st.session_state.fps_times     = []
            st.session_state.running       = True
    except Exception as e:
        st.error(f"Init error: {e}")

if stop_btn and st.session_state.running:
    st.session_state.running = False
    if st.session_state.cap:
        st.session_state.cap.release()
        st.session_state.cap = None

# ── Helper utilities ──────────────────────────────────────────────────────────

def frame_to_b64(bgr: np.ndarray) -> str:
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return base64.b64encode(buf.tobytes()).decode() if ok else ""

def annotate(frame, tracks, alert):
    color = config.BOX_COLOR_ALERT if alert else config.BOX_COLOR_NORMAL
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]
        lbl = f"#{t['track_id']}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)
        cv2.rectangle(frame, (x1, y1-th-7), (x1+tw+6, y1), color, -1)
        cv2.putText(frame, lbl, (x1+3, y1-4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255,255,255), 1, cv2.LINE_AA)
    if alert:
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, h-46), (w, h), (180,0,0), -1)
        cv2.putText(frame, "⚠ OVERCROWDING ALERT — TAKE ACTION",
                    (12, h-14), cv2.FONT_HERSHEY_DUPLEX, 0.72,
                    (255,255,255), 2, cv2.LINE_AA)
    return frame

def calc_fps(fps_times: list) -> float:
    now = time.time()
    fps_times.append(now)
    # keep only last 30 timestamps
    while len(fps_times) > 30:
        fps_times.pop(0)
    if len(fps_times) < 2:
        return 0.0
    return round((len(fps_times)-1) / (fps_times[-1]-fps_times[0]), 1)

def density_color(d):
    return {"LOW": "#2ECC71", "MEDIUM": "#F39C12", "HIGH": "#E74C3C"}.get(d, "#58A6FF")

def placeholder_frame(msg="Press  ▶ Start  to begin"):
    img = np.zeros((480, 854, 3), dtype=np.uint8)
    img[:] = (13, 17, 23)
    # Grid lines
    for x in range(0, 854, 80):
        cv2.line(img, (x, 0), (x, 480), (22, 30, 40), 1)
    for y in range(0, 480, 60):
        cv2.line(img, (0, y), (854, y), (22, 30, 40), 1)
    # Center text
    (tw, _), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_DUPLEX, 0.9, 2)
    cv2.putText(img, msg, ((854-tw)//2, 250),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, (50, 100, 180), 2, cv2.LINE_AA)
    return img

# ── Plotly chart builders ─────────────────────────────────────────────────────
_CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#8B949E", size=11),
    margin=dict(l=10, r=10, t=32, b=10),
    height=220,
    xaxis=dict(showgrid=True, gridcolor="#21262D", zeroline=False,
               color="#8B949E", tickfont=dict(size=10)),
    yaxis=dict(showgrid=True, gridcolor="#21262D", zeroline=False,
               color="#8B949E", tickfont=dict(size=10)),
)

def build_line_chart(history: list) -> go.Figure:
    n = len(history)
    xs = list(range(n))
    ys = history
    fig = go.Figure()
    if n > 1:
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color="#58A6FF", width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
            name="Count",
        ))
    layout = dict(**_CHART_LAYOUT)
    layout["title"] = dict(text="📈 People Count — Live", font=dict(size=12, color="#E6EDF3"))
    fig.update_layout(**layout)
    return fig

def build_bar_chart(tally: dict) -> go.Figure:
    cats   = ["LOW", "MEDIUM", "HIGH"]
    values = [tally[c] for c in cats]
    colors = ["#2ECC71", "#F39C12", "#E74C3C"]
    fig = go.Figure(go.Bar(
        x=cats, y=values,
        marker_color=colors,
        marker_line_width=0,
        width=0.45,
        text=values, textposition="outside",
        textfont=dict(color="#E6EDF3", size=12),
    ))
    layout = dict(**_CHART_LAYOUT)
    layout["title"] = dict(text="📊 Density Distribution", font=dict(size=12, color="#E6EDF3"))
    layout["height"] = 200
    fig.update_layout(**layout)
    return fig

# ── Fetch current values for display ─────────────────────────────────────────
count   = st.session_state.last_count
density = st.session_state.last_density
alert   = st.session_state.last_alert
peak    = st.session_state.peak_count
fps     = 0.0   # computed below when running

# ── Header ───────────────────────────────────────────────────────────────────
if st.session_state.running:
    badge = '<span class="live-badge"><span class="dot"></span>LIVE</span>'
else:
    badge = '<span class="offline-badge"><span class="dot-off"></span>OFFLINE</span>'

st.markdown(f"""
<div class="cms-header">
  <div>
    <div class="cms-title">🎯 Crowd Management System</div>
    <div class="cms-subtitle">AI-powered real-time surveillance analytics</div>
  </div>
  {badge}
</div>
""", unsafe_allow_html=True)

# ── 4 Metric cards ────────────────────────────────────────────────────────────
mc1, mc2, mc3, mc4 = st.columns(4)

dc = density_color(density)

with mc1:
    st.markdown(f"""
    <div class="metric-card card-blue">
      <div class="metric-icon">👥</div>
      <div class="metric-value" style="color:#58A6FF">{count}</div>
      <div class="metric-label">People Count</div>
      <div class="metric-sub">Currently detected</div>
    </div>""", unsafe_allow_html=True)

with mc2:
    st.markdown(f"""
    <div class="metric-card {'card-red' if density=='HIGH' else 'card-orange' if density=='MEDIUM' else 'card-green'}">
      <div class="metric-icon">{'🔴' if density=='HIGH' else '🟠' if density=='MEDIUM' else '🟢'}</div>
      <div class="metric-value" style="color:{dc}">{density}</div>
      <div class="metric-label">Crowd Density</div>
      <div class="metric-sub">LOW &lt; {config.LOW_THRESHOLD} | HIGH &gt; {config.HIGH_THRESHOLD}</div>
    </div>""", unsafe_allow_html=True)

with mc3:
    fps_val = st.session_state.get("last_fps", 0.0)
    fps_col = "#2ECC71" if fps_val >= 20 else "#F39C12" if fps_val >= 10 else "#E74C3C"
    st.markdown(f"""
    <div class="metric-card card-purple">
      <div class="metric-icon">⚡</div>
      <div class="metric-value" style="color:{fps_col}">{fps_val}</div>
      <div class="metric-label">FPS</div>
      <div class="metric-sub">Processing speed</div>
    </div>""", unsafe_allow_html=True)

with mc4:
    st.markdown(f"""
    <div class="metric-card card-orange">
      <div class="metric-icon">📌</div>
      <div class="metric-value" style="color:#F39C12">{peak}</div>
      <div class="metric-label">Peak Count</div>
      <div class="metric-sub">Session maximum</div>
    </div>""", unsafe_allow_html=True)

# ── Main section ──────────────────────────────────────────────────────────────
left_col, right_col = st.columns([3, 2], gap="medium")

with left_col:
    st.markdown('<div class="section-label">Live Video Feed</div>', unsafe_allow_html=True)
    vid_slot = st.empty()

with right_col:
    line_slot = st.empty()
    bar_slot  = st.empty()

# ── Alert section ─────────────────────────────────────────────────────────────
alert_slot = st.empty()

# ── Idle render ───────────────────────────────────────────────────────────────
def render_feed(bgr):
    b64 = frame_to_b64(bgr)
    vid_slot.markdown(f"""
    <div class="video-container">
      <div class="video-header">
        <span><span class="live-dot"></span>CAM-01 · 0.0.0.0</span>
        <span>{'🔴 RECORDING' if st.session_state.running else '⚫ STANDBY'}</span>
      </div>
      <div class="video-body"><img src="data:image/jpeg;base64,{b64}"/></div>
    </div>""", unsafe_allow_html=True)

def render_charts():
    h = st.session_state.count_history
    t = st.session_state.density_tally
    with line_slot.container():
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(build_line_chart(h[-120:] if h else []),
                        use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with bar_slot.container():
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(build_bar_chart(t),
                        use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

def render_alert(a):
    if a:
        alert_slot.markdown("""
        <div class="alert-critical">
          🚨 <span>OVERCROWDING ALERT — Crowd density exceeds safe threshold. Immediate action required.</span>
        </div>""", unsafe_allow_html=True)
    else:
        alert_slot.markdown("""
        <div class="alert-safe">
          ✅ <span>All Clear — Crowd levels within normal parameters.</span>
        </div>""", unsafe_allow_html=True)

if not st.session_state.running:
    render_feed(placeholder_frame())
    render_charts()
    render_alert(False)
    st.stop()

# ── LIVE: process one frame → rerun ──────────────────────────────────────────
cap = st.session_state.cap
ret, frame = cap.read()

if not ret:
    st.warning("⚠️ Stream ended or camera disconnected.")
    st.session_state.running = False
    cap.release()
    st.session_state.cap = None
    st.stop()

# Pipeline
t0     = time.time()
dets   = st.session_state.detector.detect(frame)
tracks = st.session_state.tracker.update(dets, frame)
result = st.session_state.analyzer.analyze(tracks)

count   = result["count"]
density = result["density"]
alert   = result["alert"]

# FPS
ft = st.session_state.fps_times
fps = calc_fps(ft)
st.session_state.fps_times = ft

# Update state
st.session_state.last_count   = count
st.session_state.last_density = density
st.session_state.last_alert   = alert
st.session_state.last_fps     = fps
if count > st.session_state.peak_count:
    st.session_state.peak_count = count
st.session_state.count_history.append(count)
st.session_state.density_tally[density] += 1
st.session_state.frame_idx += 1

# Render
frame = annotate(frame, tracks, alert)
render_feed(frame)
render_alert(alert)

# Charts every 5 frames to save CPU
if st.session_state.frame_idx % 5 == 0:
    render_charts()

time.sleep(0.04)
st.rerun()
