# api.py
import cv2
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import config
from detection import PersonDetector
from tracking import PersonTracker
from analysis import CrowdAnalyzer
import threading
import time

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared state
class GlobalState:
    def __init__(self):
        self.detector = PersonDetector()
        self.tracker = PersonTracker()
        self.analyzer = CrowdAnalyzer()
        self.latest_frame = None
        self.latest_stats = {
            "count": 0,
            "density": "LOW",
            "alert": False,
            "peak_count": 0,
            "mode": config.CURRENT_MODE,
            "fps": 0
        }
        self.running = True
        self.subscribers = []

state = GlobalState()

def process_video():
    cap = cv2.VideoCapture(config.VIDEO_SOURCE)
    frame_count = 0
    start_time = time.time()
    
    while state.running:
        success, frame = cap.read()
        if not success:
            print("[ERROR] Failed to read from video source. Retrying...")
            time.sleep(2)
            cap = cv2.VideoCapture(config.VIDEO_SOURCE)
            continue

        frame_count += 1
        if frame_count % config.FRAME_SKIP != 0:
            continue

        # Resize for performance as requested
        frame_resized = cv2.resize(frame, config.PROCESS_SIZE)
        
        # Detection & Tracking
        detections = state.detector.detect(frame_resized)
        tracks = state.tracker.update(detections, frame_resized)
        
        # Analysis
        stats = state.analyzer.analyze(tracks)
        
        # Update FPS
        curr_time = time.time()
        fps = 1 / (curr_time - start_time) if (curr_time - start_time) > 0 else 0
        start_time = curr_time
        
        # Draw on frame (only for technical modes like 'event')
        if state.latest_stats["mode"] == "event":
            for t in tracks:
                x1, y1, x2, y2 = t["bbox"]
                color = config.BOX_COLOR_ALERT if stats["alert"] else config.BOX_COLOR_NORMAL
                cv2.rectangle(frame_resized, (x1, y1), (x2, y2), color, config.BOX_THICKNESS)
                cv2.putText(frame_resized, f"ID: {t['track_id']}", (x1, y1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, color, 1)

        # Update latest state
        state.latest_stats.update(stats)
        state.latest_stats["fps"] = round(fps, 1)
        
        # Encode for MJPEG
        _, buffer = cv2.imencode('.jpg', frame_resized)
        state.latest_frame = buffer.tobytes()

    cap.release()

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=process_video, daemon=True).start()

from fastapi.responses import StreamingResponse
# ... (rest of imports)

@app.get("/video")
async def video_feed():
    def generate():
        while True:
            if state.latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + state.latest_frame + b'\r\n')
            time.sleep(0.04) # ~25 FPS sync
            
    return StreamingResponse(generate(), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get("/stats")
async def get_stats():
    return state.latest_stats

class ConfigUpdate(BaseModel):
    mode: str

@app.post("/config")
async def update_config(update: ConfigUpdate):
    if update.mode in config.MODE_CONFIGS:
        state.analyzer.update_mode(update.mode)
        state.latest_stats["mode"] = update.mode
        return {"status": "success", "mode": update.mode}
    return {"status": "error", "message": "Invalid mode"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.subscribers.append(websocket)
    try:
        while True:
            await websocket.send_json(state.latest_stats)
            await asyncio.sleep(0.5) # Update every 500ms
    except WebSocketDisconnect:
        state.subscribers.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
