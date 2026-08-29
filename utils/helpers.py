"""
utils/helpers.py
Small shared utility functions used across modules.
"""

import re
import datetime


def now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_text(text: str) -> str:
    """Normalize text coming from STT before sending to the LLM brain."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def strip_wake_word(text: str, wake_word: str) -> str:
    """Remove a leading wake word e.g. 'hey jarvis, what's the weather?' """
    pattern = rf"^(hey\s+)?{re.escape(wake_word)}[,:]?\s*"
    return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()


def bytes_to_human(n: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"
