# Crowd Control AI – Full-Stack Management System 👥

A real-time, AI-powered crowd monitoring and management system using **YOLOv8** for detection, **DeepSORT** for tracking, and a modern **FastAPI + React** stack.

---

## 🏗️ Project Structure

```
crowd_management/
├── api.py           ← FastAPI Backend (Streaming + Analytics)
├── config.py        ← Central Configuration (Thresholds & Modes)
├── detection.py     ← YOLOv8 Person Detector (with Advanced Filters)
├── tracking.py      ← DeepSORT Tracking Logic
├── analysis.py      ← Multi-mode Crowd Logic & Statistics
├── frontend/        ← React + Vite Dashboard
│   ├── src/
│   │   ├── App.jsx     # Real-time Dashboard UI
│   │   └── index.css   # Glassmorphism Design System
│   └── index.html
├── requirements.txt
└── crowd_log.csv    ← Historical Data Storage
```

---

## 🚀 Installation & Setup

### 1. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python api.py
```
*Backend runs on `http://localhost:8000`*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`*

---

## 🎯 Advanced Filtering Layer

To ensure high accuracy without retraining, the system uses a **Detection Filtering Layer**:
1. **Class Filter**: Only counts "person" (COCO Class 0).
2. **Confidence Filter**: Minimum threshold of **0.6**.
3. **Dynamic Area Filter**: Rejects noise detections smaller than **0.2%** of the frame area.
4. **Tracking Stability**: Only counts tracks after **3 frames** of consistent detection.

---

## 📊 Multi-Mode System

Toggle modes from the dashboard sidebar to adapt thresholds and insights:

| Mode | Use Case | Indicators |
|------|----------|------------|
| **Canteen** | Cafeterias | FREE, MODERATE, CROWDED |
| **Shop** | Retail Stores | LOW, MEDIUM, HIGH |
| **Event** | Large Crowds | NORMAL, BUSY, OVERCROWDED |

---

## ⚡ Features
- **Live MJPEG Stream**: Low-latency 640x480 video feed.
- **WebSocket Updates**: Real-time stat pushing to the dashboard.
- **Modern UI**: Dark theme, glassmorphism cards, and smooth animations.
- **Interactive Charts**: Historical crowd count visualization.
- **Auto-Logging**: Every reading is saved to `crowd_log.csv` for auditing.

---

## ⚙️ Configuration (`config.py`)

Edit `config.py` to change global settings like `VIDEO_SOURCE`, `FRAME_SKIP`, and `MODE_CONFIGS` (thresholds).
