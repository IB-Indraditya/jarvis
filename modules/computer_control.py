"""
modules/computer_control.py
=======================================================
Computer Control
=======================================================
- Open/close applications
- Control keyboard and mouse
- Read screen content
- Execute commands
- Manage files
- Automate repetitive tasks

NOTE: These actions touch the *host machine* running JARVIS. They are
gated behind modules/security.py (auth + permission checks) in
routes/api.py before ever being invoked. Run with the least privilege
necessary and review before enabling in production.
"""

import os
import platform
import shutil
import subprocess
from utils.logger import get_logger

logger = get_logger("jarvis.computer_control")


# ---------- Applications ----------
def open_application(app_name: str) -> str:
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(app_name)  # noqa: S606
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:  # Linux
            subprocess.Popen([app_name])
        logger.info(f"Opened application: {app_name}")
        return f"Opened {app_name}."
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to open {app_name}: {exc}")
        return f"Couldn't open {app_name}: {exc}"


def close_application(process_name: str) -> str:
    import psutil
    killed = 0
    for proc in psutil.process_iter(["pid", "name"]):
        if process_name.lower() in (proc.info["name"] or "").lower():
            try:
                proc.terminate()
                killed += 1
            except Exception:  # noqa: BLE001
                continue
    logger.info(f"Closed {killed} process(es) matching '{process_name}'")
    return f"Closed {killed} process(es) matching '{process_name}'."


# ---------- Keyboard / Mouse ----------
def type_text(text: str):
    import pyautogui
    pyautogui.typewrite(text, interval=0.02)


def press_keys(*keys):
    import pyautogui
    pyautogui.hotkey(*keys)


def move_mouse(x: int, y: int):
    import pyautogui
    pyautogui.moveTo(x, y)


def click_mouse(x: int | None = None, y: int | None = None):
    import pyautogui
    if x is not None and y is not None:
        pyautogui.click(x, y)
    else:
        pyautogui.click()


# ---------- Screen ----------
def read_screen_text() -> str:
    """OCR the current screen (delegates to modules.vision)."""
    from modules.vision import ocr_screenshot
    return ocr_screenshot()


def take_screenshot(save_path: str = "data/screenshot.png") -> str:
    import pyautogui
    img = pyautogui.screenshot()
    img.save(save_path)
    return save_path


# ---------- Shell commands ----------
def run_command(command: str, timeout: int = 15) -> dict:
    """Execute a shell command. Should only be reachable by authenticated
    admin users - see modules/security.py::require_permission."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out.", "returncode": -1}


# ---------- File management ----------
def list_dir(path: str):
    return os.listdir(path)


def move_file(src: str, dst: str):
    shutil.move(src, dst)
    return f"Moved {src} -> {dst}"


def delete_file(path: str):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
    return f"Deleted {path}"


def create_file(path: str, content: str = ""):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Created {path}"
