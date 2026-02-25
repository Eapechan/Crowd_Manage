# main.py
# ─────────────────────────────────────────────────────────────────────────────
# Entry-point for the real-time OpenCV crowd management application.
#
# Usage:
#   python main.py                    # webcam
#   python main.py --source video.mp4 # video file
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import sys
import cv2
import numpy as np

import config
from detection import PersonDetector
from tracking  import PersonTracker
from analysis  import CrowdAnalyzer


# ── Helpers ───────────────────────────────────────────────────────────────────

def draw_tracks(frame: np.ndarray, tracks: list, alert: bool) -> None:
    """
    Draw bounding boxes and track IDs on *frame* in-place.
    Box colour changes to red when an alert is active.
    """
    box_color = config.BOX_COLOR_ALERT if alert else config.BOX_COLOR_NORMAL
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]
        label = f"ID:{t['track_id']}"

        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, config.BOX_THICKNESS)

        # Label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
                                      config.FONT_SCALE, 1)
        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1),
                      box_color, -1)

        # Label text
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE,
                    config.TEXT_COLOR, 1, cv2.LINE_AA)


def draw_hud(frame: np.ndarray, result: dict) -> None:
    """
    Overlay the HUD panel (count, density, alert) onto *frame* in-place.
    """
    count   = result["count"]
    density = result["density"]
    alert   = result["alert"]

    h, w = frame.shape[:2]

    # Semi-transparent dark bar at the top
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Density colour indicator
    density_color_bgr = {
        "LOW":    (0, 200,   0),
        "MEDIUM": (0, 165, 255),
        "HIGH":   (0,   0, 255),
    }.get(density, (200, 200, 200))

    hud_text = f"People: {count}   Density: {density}"
    cv2.putText(frame, hud_text, (12, 40),
                cv2.FONT_HERSHEY_DUPLEX, 0.85,
                density_color_bgr, 2, cv2.LINE_AA)

    # Alert banner at the bottom
    if alert:
        banner = "⚠  ALERT: Overcrowding Detected!"
        cv2.rectangle(frame, (0, h - 50), (w, h), (0, 0, 180), -1)
        cv2.putText(frame, banner, (12, h - 14),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75,
                    (255, 255, 255), 2, cv2.LINE_AA)


# ── Main loop ─────────────────────────────────────────────────────────────────

def run(source) -> None:
    """Capture video, detect, track and analyse crowd continuously."""

    # ── Initialise components ─────────────────────────────────────────────────
    detector = PersonDetector()
    tracker  = PersonTracker()
    analyzer = CrowdAnalyzer()

    # ── Open video source ─────────────────────────────────────────────────────
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video source: {source}")
        sys.exit(1)

    print(f"[INFO] Video source opened: {source}")
    print("[INFO] Press  Q  to quit.")

    cv2.namedWindow(config.WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(config.WINDOW_TITLE, 1280, 720)

    frame_count = 0
    tracks = []
    result = {"count": 0, "density": "LOW", "alert": False}

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[INFO] End of video stream.")
            break
        
        frame_count += 1

        # ── Pipeline Performance Optimization ──────────────────────────────────
        # Process only every Nth frame to save CPU/GPU cycles
        if frame_count % config.FRAME_SKIP == 0:
            # Resize frame for faster inference while keeping aspect ratio
            # This helps standardise detection regardless of source resolution
            process_frame = cv2.resize(frame, config.PROCESS_SIZE)
            
            # Detect & Track
            detections = detector.detect(process_frame)
            
            # Scale detections back to original frame size for drawing
            h, w = frame.shape[:2]
            pw, ph = config.PROCESS_SIZE
            scale_x, scale_y = w / pw, h / ph
            
            scaled_detections = []
            for bbox, conf, cls in detections:
                x, y, bw, bh = bbox
                
                # Scale using floats for precision
                sx = x * scale_x
                sy = y * scale_y
                sw = bw * scale_x
                sh = bh * scale_y

                # ── Robust Clipping & Validation ─────────────────────────────
                # Ensure the scaled box is fully within the frame and has a 
                # positive area to prevent DeepSORT/OpenCV crashes.
                x1 = int(max(0, sx))
                y1 = int(max(0, sy))
                x2 = int(min(w, sx + sw))
                y2 = int(min(h, sy + sh))
                
                cw = x2 - x1
                ch = y2 - y1
                
                # Minimum size requirement for the tracking embedder (typically 4-8px)
                if cw > 5 and ch > 5:
                    scaled_bbox = [x1, y1, cw, ch]
                    scaled_detections.append((scaled_bbox, conf, cls))

            if len(scaled_detections) > 0:
                print(f"[DEBUG] Valid detections scaled: {len(scaled_detections)}")

            tracks = tracker.update(scaled_detections, frame)
            result = analyzer.analyze(tracks)

        # ── Visualise (on every frame for smoothness) ─────────────────────────
        draw_tracks(frame, tracks, result["alert"])
        draw_hud(frame, result)

        cv2.imshow(config.WINDOW_TITLE, frame)

        # Press Q or Esc to exit
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Session ended.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crowd Management System")
    parser.add_argument(
        "--source",
        default=config.VIDEO_SOURCE,
        help="Video source: integer (webcam index) or path to a video file.",
    )
    args = parser.parse_args()

    # Allow integer webcam indices passed as strings (e.g. --source 0)
    source = args.source
    try:
        source = int(source)
    except (ValueError, TypeError):
        pass  # keep as string (file path)

    run(source)
