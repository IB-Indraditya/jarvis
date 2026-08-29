"""
modules/vision.py
=======================================================
Computer Vision
=======================================================
- Object detection
- Face detection
- OCR / text recognition
- Image analysis
- Camera monitoring
"""

import cv2
import numpy as np
from utils.logger import get_logger

logger = get_logger("jarvis.vision")

_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def detect_faces(image_path: str) -> list[dict]:
    img = cv2.imread(image_path)
    if img is None:
        return []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    return [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x, y, w, h) in faces]


def recognize_known_face(image_path: str, known_encodings: dict) -> str | None:
    """known_encodings: {name: face_recognition.face_encoding}. Requires the
    `face_recognition` package (dlib-based)."""
    try:
        import face_recognition
        img = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            return None
        for name, known in known_encodings.items():
            if face_recognition.compare_faces([known], encodings[0])[0]:
                return name
        return "unknown"
    except Exception as exc:  # noqa: BLE001
        logger.error(f"recognize_known_face failed: {exc}")
        return None


def detect_objects(image_path: str) -> list[dict]:
    """Lightweight edge/contour-based object detector as a dependency-free
    placeholder. Swap in a YOLO/ONNX model for real object detection."""
    img = cv2.imread(image_path)
    if img is None:
        return []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        if cv2.contourArea(c) < 500:
            continue
        x, y, w, h = cv2.boundingRect(c)
        boxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
    return boxes


def ocr_image(image_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(image_path))
    except Exception as exc:  # noqa: BLE001
        logger.error(f"OCR failed: {exc}")
        return ""


def ocr_screenshot() -> str:
    from modules.computer_control import take_screenshot
    path = take_screenshot()
    return ocr_image(path)


def analyze_image(image_path: str) -> dict:
    img = cv2.imread(image_path)
    if img is None:
        return {"error": "could not read image"}
    h, w = img.shape[:2]
    avg_color = img.mean(axis=(0, 1)).tolist()  # BGR
    return {
        "width": w,
        "height": h,
        "avg_color_bgr": avg_color,
        "faces": len(detect_faces(image_path)),
    }


def camera_frame_generator(camera_index: int = 0):
    """Generator yielding JPEG-encoded frames for MJPEG streaming
    (used by routes/api.py for a live camera-monitoring endpoint)."""
    cap = cv2.VideoCapture(camera_index)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            _, buf = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
    finally:
        cap.release()
