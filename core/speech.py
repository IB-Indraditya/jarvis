"""
core/speech.py
=======================================================
Speech-to-Text / Text-to-Speech / Voice Commands
=======================================================

Features:
    - SpeechRecognition microphone input
    - Google Web Speech recognition
    - Offline pyttsx3 TTS
    - Male / female voice selection
    - Voice rate and volume control
    - Immediate speech stop
    - Thread-safe TTS control

Configuration comes from config.py:

    JARVIS_VOICE_GENDER
    JARVIS_VOICE_RATE
    JARVIS_VOICE_VOLUME
"""


import threading

from config import Config
from utils.logger import get_logger


logger = get_logger("jarvis.speech")


# ============================================================
# SPEECH TO TEXT
# ============================================================

class SpeechToText:

    def __init__(self):

        try:

            import speech_recognition as sr

            self.sr = sr
            self.recognizer = sr.Recognizer()
            self.available = True

            logger.info(
                "SpeechRecognition initialized."
            )

        except ImportError:

            logger.warning(
                "SpeechRecognition not installed - STT disabled."
            )

            self.available = False

    # ========================================================
    # TRANSCRIBE FILE
    # ========================================================

    def transcribe_file(
        self,
        audio_path: str
    ) -> str:

        if not self.available:
            return ""

        try:

            with self.sr.AudioFile(
                audio_path
            ) as source:

                audio = self.recognizer.record(
                    source
                )

            return self.recognizer.recognize_google(
                audio
            )

        except Exception as exc:

            logger.error(
                f"STT failed: {exc}"
            )

            return ""

    # ========================================================
    # MICROPHONE
    # ========================================================

    def listen_from_microphone(
        self,
        timeout: int = 5
    ) -> str:

        if not self.available:
            return ""

        try:

            with self.sr.Microphone() as source:

                logger.info(
                    "Listening..."
                )

                self.recognizer.adjust_for_ambient_noise(
                    source
                )

                audio = self.recognizer.listen(
                    source,
                    timeout=timeout
                )

            text = self.recognizer.recognize_google(
                audio
            )

            logger.info(
                f"Heard: {text}"
            )

            return text

        except Exception as exc:

            logger.error(
                f"STT failed: {exc}"
            )

            return ""


# ============================================================
# TEXT TO SPEECH
# ============================================================

class TextToSpeech:

    def __init__(
        self,
        rate: int | None = None,
        volume: float | None = None,
        gender: str | None = None
    ):

        # ----------------------------------------------------
        # Configuration
        # ----------------------------------------------------

        self.rate = (
            rate
            if rate is not None
            else Config.JARVIS_VOICE_RATE
        )

        self.volume = (
            volume
            if volume is not None
            else Config.JARVIS_VOICE_VOLUME
        )

        self.gender = (
            gender
            if gender
            else Config.JARVIS_VOICE_GENDER
        ).lower().strip()

        # ----------------------------------------------------
        # Thread control
        # ----------------------------------------------------

        self.lock = threading.Lock()

        self.engine = None

        self.available = False

        # Used to prevent queued speech after stop
        self.stop_requested = False

        # ----------------------------------------------------
        # Initialize
        # ----------------------------------------------------

        self._initialize()

    # ========================================================
    # INITIALIZE
    # ========================================================

    def _initialize(self):

        try:

            import pyttsx3

            self.engine = pyttsx3.init()

            self.engine.setProperty(
                "rate",
                self.rate
            )

            self.engine.setProperty(
                "volume",
                self.volume
            )

            self.available = True

            # Select voice
            self.set_voice(
                self.gender
            )

            logger.info(
                "pyttsx3 TTS initialized."
            )

        except Exception as exc:

            logger.warning(
                f"pyttsx3 not available - TTS disabled: {exc}"
            )

            self.available = False

    # ========================================================
    # GET VOICES
    # ========================================================

    def get_voices(self):

        if not self.available:
            return []

        try:

            return self.engine.getProperty(
                "voices"
            )

        except Exception:

            return []

    # ========================================================
    # LIST VOICES
    # ========================================================

    def list_voices(self):

        voices = self.get_voices()

        result = []

        for index, voice in enumerate(voices):

            result.append({
                "index": index,
                "id": getattr(
                    voice,
                    "id",
                    ""
                ),
                "name": getattr(
                    voice,
                    "name",
                    ""
                ),
                "gender": getattr(
                    voice,
                    "gender",
                    ""
                )
            })

        return result

    # ========================================================
    # SET VOICE
    # ========================================================

    def set_voice(
        self,
        gender: str
    ) -> bool:

        if not self.available:
            return False

        gender = (
            gender
            .lower()
            .strip()
        )

        if gender not in (
            "male",
            "female"
        ):

            logger.warning(
                f"Invalid voice gender: {gender}"
            )

            return False

        try:

            voices = self.get_voices()

            if not voices:

                logger.warning(
                    "No system voices found."
                )

                return False

            # ------------------------------------------------
            # Voice keywords
            # ------------------------------------------------

            male_keywords = [
                "male",
                "david",
                "mark",
                "george",
                "guy",
                "ryan",
                "alex",
                "daniel",
                "james",
                "richard",
            ]

            female_keywords = [
                "female",
                "zira",
                "susan",
                "hazel",
                "samantha",
                "aria",
                "jenny",
                "libby",
                "sara",
                "emily",
            ]

            keywords = (
                male_keywords
                if gender == "male"
                else female_keywords
            )

            selected = None

            # ------------------------------------------------
            # Find matching voice
            # ------------------------------------------------

            for voice in voices:

                voice_id = str(
                    getattr(
                        voice,
                        "id",
                        ""
                    )
                ).lower()

                voice_name = str(
                    getattr(
                        voice,
                        "name",
                        ""
                    )
                ).lower()

                voice_gender = str(
                    getattr(
                        voice,
                        "gender",
                        ""
                    )
                ).lower()

                searchable = (
                    voice_id
                    + " "
                    + voice_name
                    + " "
                    + voice_gender
                )

                if any(
                    keyword in searchable
                    for keyword in keywords
                ):

                    selected = voice
                    break

            # ------------------------------------------------
            # Fallback
            # ------------------------------------------------

            if selected is None:

                if gender == "female":

                    selected = voices[0]

                elif len(voices) > 1:

                    selected = voices[1]

                else:

                    selected = voices[0]

            # ------------------------------------------------
            # Apply
            # ------------------------------------------------

            self.engine.setProperty(
                "voice",
                selected.id
            )

            self.gender = gender

            logger.info(
                f"Selected {gender} voice: "
                f"{getattr(selected, 'name', selected.id)}"
            )

            return True

        except Exception as exc:

            logger.error(
                f"Voice selection failed: {exc}"
            )

            return False

    # ========================================================
    # SET RATE
    # ========================================================

    def set_rate(
        self,
        rate: int
    ) -> bool:

        if not self.available:
            return False

        try:

            self.rate = int(rate)

            self.engine.setProperty(
                "rate",
                self.rate
            )

            return True

        except Exception as exc:

            logger.error(
                f"Failed to set speech rate: {exc}"
            )

            return False

    # ========================================================
    # SET VOLUME
    # ========================================================

    def set_volume(
        self,
        volume: float
    ) -> bool:

        if not self.available:
            return False

        try:

            volume = max(
                0.0,
                min(1.0, float(volume))
            )

            self.volume = volume

            self.engine.setProperty(
                "volume",
                self.volume
            )

            return True

        except Exception as exc:

            logger.error(
                f"Failed to set volume: {exc}"
            )

            return False

    # ========================================================
    # SPEAK
    # ========================================================

    def speak(
        self,
        text: str
    ):

        if not text:
            return

        if not self.available:

            logger.info(
                f"[TTS disabled] Would say: {text}"
            )

            return

        # ----------------------------------------------------
        # New speech cancels previous stop state
        # ----------------------------------------------------

        self.stop_requested = False

        try:

            with self.lock:

                if self.stop_requested:
                    return

                self.engine.say(
                    text
                )

                self.engine.runAndWait()

        except Exception as exc:

            logger.error(
                f"TTS failed: {exc}"
            )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        """
        Immediately stop current speech.
        """

        self.stop_requested = True

        if not self.available:
            return

        try:

            self.engine.stop()

            logger.info(
                "JARVIS speech stopped."
            )

        except Exception as exc:

            logger.error(
                f"Failed to stop speech: {exc}"
            )

    # ========================================================
    # IS SPEAKING
    # ========================================================

    def is_speaking(self) -> bool:

        if not self.available:
            return False

        try:

            return bool(
                self.engine.isBusy()
            )

        except Exception:

            return False