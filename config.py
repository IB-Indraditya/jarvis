"""
config.py
=======================================================
Central configuration for the JARVIS Flask application.
All configurable values are loaded from environment
variables (.env).
=======================================================
"""

import os
from dotenv import load_dotenv


# =======================================================
# LOAD ENVIRONMENT VARIABLES
# =======================================================

load_dotenv()


# =======================================================
# BASE DIRECTORIES
# =======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

LOG_DIR = os.path.join(
    DATA_DIR,
    "logs"
)

DB_PATH = os.path.join(
    DATA_DIR,
    "jarvis.db"
)


# Create required directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# =======================================================
# CONFIGURATION
# =======================================================

class Config:

    # ===================================================
    # FLASK
    # ===================================================

    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY",
        "dev-secret-key"
    )

    DEBUG = os.getenv(
        "FLASK_DEBUG",
        "1"
    ) == "1"

    HOST = os.getenv(
        "HOST",
        "0.0.0.0"
    )

    PORT = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )


    # ===================================================
    # GEMINI AI / LLM
    # ===================================================

    GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY",
        ""
    )

    # Primary model
    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite"
    )

    # ---------------------------------------------------
    # Gemini fallback models
    #
    # brain.py can use these when the primary model
    # returns quota/rate-limit/model-not-found errors.
    # ---------------------------------------------------

    GEMINI_FALLBACK_MODELS = [
        model.strip()
        for model in os.getenv(
            "GEMINI_FALLBACK_MODELS",
            "gemini-3.5-flash,"
            "gemini-3.5-flash-lite,"
            "gemini-2.5-flash,"
            "gemini-2.5-flash-lite"
        ).split(",")
        if model.strip()
    ]


    # Maximum number of model attempts
    GEMINI_MAX_MODEL_ATTEMPTS = int(
        os.getenv(
            "GEMINI_MAX_MODEL_ATTEMPTS",
            "5"
        )
    )


    # ===================================================
    # JARVIS PERSONA
    # ===================================================

    JARVIS_NAME = os.getenv(
        "JARVIS_NAME",
        "JARVIS"
    )


    # ===================================================
    # VOICE / TEXT TO SPEECH
    # ===================================================

    # Available:
    #
    #     male
    #     female
    #
    JARVIS_VOICE_GENDER = os.getenv(
        "JARVIS_VOICE_GENDER",
        "female"
    ).lower().strip()


    # Speech speed
    #
    # Typical pyttsx3 values:
    #
    #     120 = slow
    #     150 = normal
    #     175 = normal/fast
    #     200 = fast
    #
    JARVIS_VOICE_RATE = int(
        os.getenv(
            "JARVIS_VOICE_RATE",
            "175"
        )
    )


    # Volume
    #
    # Range:
    #     0.0 - 1.0
    #
    JARVIS_VOICE_VOLUME = float(
        os.getenv(
            "JARVIS_VOICE_VOLUME",
            "1.0"
        )
    )


    # ===================================================
    # WAKE WORD
    # ===================================================

    WAKE_WORD = os.getenv(
        "WAKE_WORD",
        "jarvis"
    ).lower().strip()


    # Porcupine Access Key
    #
    # Leave empty if you aren't using Porcupine.
    #
    PORCUPINE_ACCESS_KEY = os.getenv(
        "PORCUPINE_ACCESS_KEY",
        ""
    )


    # ===================================================
    # LOCAL COMMANDS
    # ===================================================

    # Commands that must NEVER be sent to Gemini.
    #
    # Particularly important for:
    #
    #     stop
    #     jarvis stop
    #
    # These should be handled locally.
    #

    STOP_COMMANDS = {
        "stop",
        "jarvis stop",
        "stop jarvis",
        "stop talking",
        "stop speaking",
        "be quiet",
        "quiet",
        "silence",
        "shut up",
    }


    # ===================================================
    # INFORMATION RETRIEVAL
    # ===================================================

    WEATHER_API_KEY = os.getenv(
        "WEATHER_API_KEY",
        ""
    )

    NEWS_API_KEY = os.getenv(
        "NEWS_API_KEY",
        ""
    )


    # ===================================================
    # EMAIL / SMTP
    # ===================================================

    SMTP_HOST = os.getenv(
        "SMTP_HOST",
        ""
    )

    SMTP_PORT = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    SMTP_USER = os.getenv(
        "SMTP_USER",
        ""
    )

    SMTP_PASS = os.getenv(
        "SMTP_PASS",
        ""
    )


    # ===================================================
    # MQTT / IoT
    # ===================================================

    MQTT_BROKER = os.getenv(
        "MQTT_BROKER",
        "localhost"
    )

    MQTT_PORT = int(
        os.getenv(
            "MQTT_PORT",
            "1883"
        )
    )

    MQTT_USER = os.getenv(
        "MQTT_USER",
        ""
    )

    MQTT_PASS = os.getenv(
        "MQTT_PASS",
        ""
    )


    # ===================================================
    # SECURITY
    # ===================================================

    ADMIN_PASSWORD = os.getenv(
        "JARVIS_ADMIN_PASSWORD",
        "change-me"
    )


    # ===================================================
    # PATHS
    # ===================================================

    DATA_DIR = DATA_DIR

    LOG_DIR = LOG_DIR

    DB_PATH = DB_PATH


# =======================================================
# OPTIONAL DEBUG INFORMATION
# =======================================================

if __name__ == "__main__":

    print("========================================")
    print("       JARVIS CONFIGURATION")
    print("========================================")

    print(
        "Gemini API:",
        "Configured" if Config.GEMINI_API_KEY else "Not configured"
    )

    print(
        "Primary model:",
        Config.GEMINI_MODEL
    )

    print(
        "Fallback models:",
        Config.GEMINI_FALLBACK_MODELS
    )

    print(
        "Voice:",
        Config.JARVIS_VOICE_GENDER
    )

    print(
        "Voice rate:",
        Config.JARVIS_VOICE_RATE
    )

    print(
        "Wake word:",
        Config.WAKE_WORD
    )

    print(
        "Porcupine:",
        "Configured"
        if Config.PORCUPINE_ACCESS_KEY
        else "Not configured"
    )

    print("========================================")