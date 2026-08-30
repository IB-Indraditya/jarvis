"""
routes/api.py
=======================================================
REST API blueprint - wires the HTML/JS dashboard (templates/index.html)
to every JARVIS module: brain, memory, speech, system monitor,
computer control, info retrieval, IoT, security, automation, vision.
"""

import os
from flask import Blueprint, request, jsonify, Response, send_file

from core.brain import JarvisBrain
from core.memory import Memory
from core.speech import SpeechToText, TextToSpeech
from core.wake_word import SimpleTextWakeWord

from modules import (
    system_monitor,
    computer_control,
    info_retrieval,
    iot_control,
    security,
    automation,
    vision,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

brain = JarvisBrain()
memory = Memory()
stt = SpeechToText()
tts = TextToSpeech()
wake = SimpleTextWakeWord()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# 1. AI / LLM Brain + Voice commands
# ============================================================
@api_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    text = data.get("message", "")
    session_id = data.get("session_id", "default")

    if wake.detected(text):
        text = wake.strip(text)

    reply = brain.ask(text, session_id=session_id)
    return jsonify({"reply": reply})


@api_bp.route("/voice/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "no audio file"}), 400
    f = request.files["audio"]
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)
    text = stt.transcribe_file(path)
    return jsonify({"text": text})


@api_bp.route("/voice/speak", methods=["POST"])
def speak():
    data = request.get_json(force=True)
    text = data.get("text", "")
    tts.speak(text)
    return jsonify({"status": "spoken"})


# ============================================================
# 2. System monitoring
# ============================================================
@api_bp.route("/system/snapshot", methods=["GET"])
def system_snapshot():
    return jsonify(system_monitor.full_snapshot())


# ============================================================
# 3. Computer control
# ============================================================
@api_bp.route("/computer/open", methods=["POST"])
@security.require_permission("open_application")
def open_app():
    app_name = request.get_json(force=True).get("app_name", "")
    return jsonify({"result": computer_control.open_application(app_name)})


@api_bp.route("/computer/close", methods=["POST"])
@security.require_permission("close_application")
def close_app():
    process_name = request.get_json(force=True).get("process_name", "")
    return jsonify({"result": computer_control.close_application(process_name)})


@api_bp.route("/computer/run", methods=["POST"])
@security.require_permission("run_command")
def run_cmd():
    command = request.get_json(force=True).get("command", "")
    return jsonify(computer_control.run_command(command))


@api_bp.route("/computer/files", methods=["GET"])
def list_files():
    path = request.args.get("path", ".")
    try:
        return jsonify({"files": computer_control.list_dir(path)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400


@api_bp.route("/computer/files/delete", methods=["POST"])
@security.require_permission("delete_file")
def delete_file_route():
    path = request.get_json(force=True).get("path", "")
    return jsonify({"result": computer_control.delete_file(path)})


@api_bp.route("/computer/screenshot", methods=["GET"])
def screenshot():
    path = computer_control.take_screenshot()
    return send_file(path, mimetype="image/png")


# ============================================================
# 4. Information retrieval
# ============================================================
# @api_bp.route("/info/search", methods=["GET"])
# def search():
#     q = request.args.get("q", "")
#     return jsonify({"results": info_retrieval.web_search(q)})

@api_bp.route("/info/search", methods=["GET"])
def search():
    q = request.args.get("q", "")
    return jsonify({
        "results": info_retrieval.web_search(q)
    })

@api_bp.route("/info/weather", methods=["GET"])
def weather():
    city = request.args.get("city", "Kolkata")
    return jsonify(info_retrieval.get_weather(city))


@api_bp.route("/info/news", methods=["GET"])
def news():
    topic = request.args.get("topic", "technology")
    return jsonify({"articles": info_retrieval.get_news(topic)})


@api_bp.route("/info/wikipedia", methods=["GET"])
def wiki():
    q = request.args.get("q", "")
    return jsonify({"summary": info_retrieval.wikipedia_summary(q)})


# ============================================================
# 5. Home / IoT control
# ============================================================
@api_bp.route("/iot/devices", methods=["GET"])
def iot_devices():
    return jsonify(iot_control.list_devices())


@api_bp.route("/iot/set", methods=["POST"])
def iot_set():
    data = request.get_json(force=True)
    return jsonify(iot_control.set_device(data["device_id"], data["state"]))


# ============================================================
# 6. Security
# ============================================================
@api_bp.route("/auth/login", methods=["POST"])
def login():
    password = request.get_json(force=True).get("password", "")
    token = security.authenticate(password)
    if not token:
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"token": token})


@api_bp.route("/auth/logout", methods=["POST"])
def logout_route():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    security.logout(token)
    return jsonify({"status": "logged out"})


# ============================================================
# 7. Automation
# ============================================================
@api_bp.route("/automation/reminders", methods=["GET", "POST"])
def reminders():
    if request.method == "POST":
        title = request.get_json(force=True).get("title", "")
        task_id = automation.create_reminder(title)
        return jsonify({"id": task_id})
    return jsonify({"reminders": automation.list_reminders()})


@api_bp.route("/automation/reminders/<int:task_id>/complete", methods=["POST"])
def complete_reminder_route(task_id):
    automation.complete_reminder(task_id)
    return jsonify({"status": "completed"})


@api_bp.route("/automation/email", methods=["POST"])
def email_route():
    data = request.get_json(force=True)
    ok = automation.send_email(data["to"], data["subject"], data["body"])
    return jsonify({"sent": ok})


@api_bp.route("/automation/report", methods=["GET"])
def report_route():
    return jsonify({"report": automation.generate_daily_report()})


# ============================================================
# 8. Computer vision
# ============================================================
@api_bp.route("/vision/analyze", methods=["POST"])
def vision_analyze():
    if "image" not in request.files:
        return jsonify({"error": "no image file"}), 400
    f = request.files["image"]
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)
    return jsonify(vision.analyze_image(path))


@api_bp.route("/vision/ocr", methods=["POST"])
def vision_ocr():
    if "image" not in request.files:
        return jsonify({"error": "no image file"}), 400
    f = request.files["image"]
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)
    return jsonify({"text": vision.ocr_image(path)})


@api_bp.route("/vision/camera_feed")
def camera_feed():
    return Response(
        vision.camera_frame_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ============================================================
# 9. Personal memory
# ============================================================
@api_bp.route("/memory/preferences", methods=["GET", "POST"])
def preferences():
    if request.method == "POST":
        data = request.get_json(force=True)
        memory.set_preference(data["key"], data["value"])
        return jsonify({"status": "saved"})
    return jsonify(memory.all_preferences())


@api_bp.route("/memory/conversation/<session_id>", methods=["GET", "DELETE"])
def conversation(session_id):
    if request.method == "DELETE":
        memory.clear_session(session_id)
        return jsonify({"status": "cleared"})
    return jsonify({"history": memory.get_recent(session_id, limit=50)})
