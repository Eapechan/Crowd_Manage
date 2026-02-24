# Crowd Management System 👥

A real-time crowd detection, tracking, and density analysis system powered by **YOLOv8** and **DeepSORT**.

---

## Project Structure

```
crowd_management/
├── config.py       ← All configurable thresholds & settings
├── detection.py    ← YOLOv8 person detector
├── tracking.py     ← DeepSORT unique-ID tracker
├── analysis.py     ← Crowd density classifier + CSV logger
├── main.py         ← Real-time OpenCV window app
├── app.py          ← Streamlit web dashboard
└── requirements.txt
```

---

## Installation

```bash
# 1. Create & activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt
```

> **Note:** The first run downloads the YOLOv8n weights (~6 MB) automatically.

---

## How to Run

### Option A – OpenCV Window (Real-time)

```bash
# Webcam (default)
python main.py

# Video file
python main.py --source path/to/video.mp4
```

**Controls:** Press `Q` or `Esc` to quit.

### Option B – Streamlit Dashboard

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.  
Use the sidebar to choose the camera/file source, adjust thresholds, and click **▶ Start**.

---

## Configuration (`config.py`)

| Parameter           | Default          | Description                                   |
|---------------------|------------------|-----------------------------------------------|
| `MODEL_NAME`        | `yolov8n.pt`     | YOLOv8 variant (`n` / `s` / `m`)              |
| `CONFIDENCE_THRESHOLD` | `0.4`         | Minimum detection confidence                  |
| `VIDEO_SOURCE`      | `0`              | Webcam index or video file path               |
| `LOW_THRESHOLD`     | `10`             | People < 10 → **LOW** density                 |
| `HIGH_THRESHOLD`    | `25`             | People > 25 → **HIGH** density                |
| `ALERT_THRESHOLD`   | `25`             | Count that triggers the overcrowding alert    |
| `ENABLE_CSV_LOGGING`| `True`           | Append readings to `crowd_log.csv`            |

---

## Features

| Feature                      | OpenCV (`main.py`) | Streamlit (`app.py`) |
|------------------------------|--------------------|----------------------|
| Live video feed              | ✅                  | ✅                   |
| Bounding boxes + IDs         | ✅                  | ✅                   |
| People count HUD             | ✅                  | ✅                   |
| Density classification       | ✅                  | ✅                   |
| Overcrowding alert           | ✅ (red banner)    | ✅ (alert card)       |
| Count history chart          | ❌                  | ✅                   |
| Configurable thresholds UI   | ❌                  | ✅ (sidebar sliders)  |
| CSV logging                  | ✅                  | ✅                   |

---

## Crowd Density Classification

| Level       | Condition              | Colour   |
|-------------|------------------------|----------|
| 🟢 LOW     | count < `LOW_THRESHOLD`  | Green    |
| 🟠 MEDIUM  | `LOW` ≤ count ≤ `HIGH` | Orange   |
| 🔴 HIGH    | count > `HIGH_THRESHOLD` | Red      |

An **alert** fires whenever count exceeds `ALERT_THRESHOLD`.

---

## Output Files

- **`crowd_log.csv`** – timestamped log of every reading:
  ```
  timestamp,count,density,alert
  2026-02-24 21:20:00,8,LOW,0
  2026-02-24 21:20:01,27,HIGH,1
  ```

---

## Troubleshooting

| Issue                        | Fix                                           |
|------------------------------|-----------------------------------------------|
| Camera not opening           | Check index or file path in `config.py`       |
| Slow on CPU                  | Switch to `yolov8n.pt` (default, fastest)     |
| `deep_sort_realtime` import error | `pip install deep-sort-realtime`        |
| Streamlit blank screen       | Click **▶ Start** in the sidebar              |
