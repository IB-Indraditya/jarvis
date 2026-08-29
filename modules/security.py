"""
modules/security.py
=======================================================
Security
=======================================================
- User authentication
- Voice/face recognition (see modules/vision.py for the face part)
- Permission management
- Activity logging
- Alerts
"""

import functools
import hashlib
import secrets
from flask import session, jsonify, request
from config import Config
from core.memory import Memory
from utils.logger import get_logger

logger = get_logger("jarvis.security")
memory = Memory()

_active_tokens = set()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(password: str) -> str | None:
    """Very small password-based auth for a single-user desktop assistant.
    Swap for proper multi-user auth (e.g. Flask-Login) if needed."""
    if hash_password(password) == hash_password(Config.ADMIN_PASSWORD):
        token = secrets.token_hex(16)
        _active_tokens.add(token)
        log_activity("auth.login.success")
        return token
    log_activity("auth.login.failed")
    return None


def is_authenticated(token: str | None) -> bool:
    return bool(token) and token in _active_tokens


def logout(token: str):
    _active_tokens.discard(token)
    log_activity("auth.logout")


def require_auth(view_func):
    """Decorator for Flask routes that need a valid bearer token."""
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not is_authenticated(token):
            return jsonify({"error": "unauthorized"}), 401
        return view_func(*args, **kwargs)
    return wrapper


# ---------- Permission management ----------
DANGEROUS_ACTIONS = {"run_command", "delete_file", "close_application"}


def require_permission(action: str):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            if action in DANGEROUS_ACTIONS:
                token = request.headers.get("Authorization", "").replace("Bearer ", "")
                if not is_authenticated(token):
                    log_activity(f"permission.denied:{action}")
                    return jsonify({"error": f"Action '{action}' requires authentication."}), 403
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


# ---------- Activity logging & alerts ----------
def log_activity(event: str, detail: str = ""):
    logger.info(f"ACTIVITY | {event} | {detail}")
    memory.set_preference(f"last_activity", f"{event} {detail}".strip())


def raise_alert(message: str, level: str = "warning"):
    logger.warning(f"ALERT[{level}] {message}")
    # Hook this up to email / push notification / IoT siren etc.
    return {"alert": message, "level": level}
