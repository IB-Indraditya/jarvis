# J.A.R.V.I.S — Flask AI Assistant OS

A modular, JARVIS-style personal AI assistant built with **Flask** and
**Google Gemini** (`google-genai`), styled after an Iron-Man-esque HUD
dashboard.

## Project structure

```
jarvis/
├── app.py                  # Flask entry point
├── config.py                # Central config (reads .env)
├── requirements.txt
├── .env.example
├── core/                    # The "brain" and always-on services
│   ├── brain.py              # AI / LLM brain (google.genai wrapper)
│   ├── memory.py              # Personal memory (SQLite)
│   ├── speech.py               # Speech-to-text / Text-to-speech
│   └── wake_word.py             # "Hey Jarvis" wake-word detection
├── modules/                  # Feature modules (tools the brain can use)
│   ├── system_monitor.py       # CPU / RAM / Disk / Battery / Temps
│   ├── computer_control.py     # Apps, keyboard/mouse, files, shell
│   ├── info_retrieval.py       # Web search, weather, news, Wikipedia, maps
│   ├── iot_control.py          # Lights, fans, plugs, thermostats via MQTT
│   ├── security.py             # Auth, permissions, activity log, alerts
│   ├── automation.py           # Scheduler, reminders, email, reports
│   └── vision.py               # Face/object detection, OCR, camera feed
├── routes/
│   └── api.py                # REST API blueprint tying it all together
├── templates/
│   └── index.html            # HUD dashboard UI
├── static/
│   ├── css/style.css
│   └── js/main.js
├── examples/
│   └── quickstart_gemini.py  # Minimal google-genai usage example
├── utils/
│   ├── logger.py
│   └── helpers.py
└── data/                     # SQLite DB + logs (created at runtime)
```

## Setup

```bash
cd jarvis
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# then edit .env and set GEMINI_API_KEY (and any optional keys)

python app.py
```

Visit **http://localhost:5000** for the dashboard.

Tested with **Python 3.14**. `requirements.txt` uses minimum versions
(`>=`) rather than hard pins, so pip picks whatever build has a
prebuilt wheel for your Python version instead of compiling an old
release from source.

### Optional: face recognition

`face_recognition` (and its dependency `dlib`) is **not** in the core
`requirements.txt` because dlib is a compiled C++ library that rarely
has a prebuilt wheel for brand-new Python releases and needs a full
C++ build toolchain to compile from source. The app runs fine without
it — `modules/vision.py::recognize_known_face` checks for it and
degrades gracefully if it's missing. If you want it:

```bash
pip install -r requirements-optional.txt
```

If that fails to build, the most reliable fix is a separate venv on
Python 3.11 or 3.12, where prebuilt dlib wheels are far more common.

## Voice (Speech-to-Text / Text-to-Speech / Wake word)

The dashboard's mic button, "Hey Jarvis" wake-word toggle, and spoken
replies all run **in the browser** via the Web Speech API
(`SpeechRecognition` for STT, `speechSynthesis` for TTS) — see
`static/js/main.js`. This needs zero server audio setup and works the
moment you open the page in Chrome or Edge (Firefox/Safari have
limited/no `SpeechRecognition` support, so voice input falls back to
the text box there while typing always works everywhere).

- Click the **mic button** for a single push-to-talk command.
- Click **"Hey Jarvis"** to enable always-listening wake-word mode —
  JARVIS ignores everything until it hears "Hey Jarvis" or "Jarvis",
  then treats what follows as your command.
- Click **"Speak"** to toggle whether replies are read aloud.
- The central orb changes state (idle / listening / thinking /
  speaking) and its ring reacts to your live microphone volume while
  listening.

Separately, `core/speech.py` + `/api/voice/transcribe` and
`/api/voice/speak` expose **server-side** STT/TTS (SpeechRecognition
+ pyttsx3) for automation use cases — e.g. a background script that
listens on the JARVIS host machine's own microphone/speakers rather
than a browser tab. Both paths are independent; use whichever fits
your deployment.

## The core AI call

`core/brain.py` wraps the exact pattern this project is built around:

```python
import google.genai as g

obj = g.Client(api_key=key)
response = obj.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Explain quantum computing'
)
print(response.text)
```

`JarvisBrain.ask()` extends this with conversation memory, a JARVIS
persona/system prompt, and error handling. `JarvisBrain.quick()` exposes
the bare, one-off version if you just want a single completion.

## Main components (mapped to files)

| Component | Where |
|---|---|
| Speech-to-text / Text-to-speech / Wake word / Voice commands | `core/speech.py`, `core/wake_word.py` |
| AI / LLM Brain | `core/brain.py` |
| Computer Control | `modules/computer_control.py` |
| System Monitoring | `modules/system_monitor.py` |
| Information Retrieval | `modules/info_retrieval.py` |
| Home / IoT Control | `modules/iot_control.py` |
| Security | `modules/security.py` |
| Automation | `modules/automation.py` |
| Computer Vision | `modules/vision.py` |
| Personal Memory | `core/memory.py` |

All of the above are exposed over HTTP via `routes/api.py` (see that
file for the full endpoint list: `/api/chat`, `/api/system/snapshot`,
`/api/computer/*`, `/api/info/*`, `/api/iot/*`, `/api/auth/*`,
`/api/automation/*`, `/api/vision/*`, `/api/memory/*`).

## Notes on optional dependencies

Some modules (speech, computer control, vision, wake word) depend on
packages that need OS-level libraries (`pyaudio`, `dlib` for
`face_recognition`, `tesseract-ocr` for `pytesseract`, etc). Every
module is written to **fail gracefully** — if a dependency or piece of
hardware (microphone, camera, MQTT broker) isn't available, that
feature logs a warning and returns a safe default instead of crashing
the whole app, so you can enable pieces incrementally.

## Security notice

`modules/computer_control.py` can execute shell commands, delete
files, and close applications on the host machine. These routes are
gated behind `modules/security.py::require_permission`, which requires
a valid auth token (`POST /api/auth/login` with `JARVIS_ADMIN_PASSWORD`
from `.env`). Review and harden this before exposing JARVIS beyond
your local machine.
