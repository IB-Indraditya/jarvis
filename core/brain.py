"""
core/brain.py
=======================================================
JARVIS AI / LLM Brain
=======================================================

Features:
    - Google Gemini integration
    - Automatic model fallback
    - Conversation memory
    - Local stop commands
    - Text-to-speech using pyttsx3
    - Male / female voice selection
    - Voice speed and volume control
    - Graceful API error handling

IMPORTANT:
    Local commands such as "stop" are handled BEFORE
    Gemini is contacted.

Example:

    from core.brain import JarvisBrain

    brain = JarvisBrain()

    reply = brain.ask(
        "Explain quantum computing",
        session_id="default"
    )

    print(reply)

    brain.speak(reply)
"""


# ============================================================
# IMPORTS
# ============================================================

import google.genai as g

from config import Config
from core.memory import Memory
from utils.logger import get_logger


# ============================================================
# OPTIONAL TEXT-TO-SPEECH
# ============================================================

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


# ============================================================
# LOGGER
# ============================================================

logger = get_logger("jarvis.brain")


# ============================================================
# JARVIS PERSONA
# ============================================================

SYSTEM_PERSONA = """
You are JARVIS, a helpful, concise, slightly witty personal AI
assistant embedded in a desktop control-center application.

You can discuss:

- system status
- files
- automation
- smart-home devices
- programming
- technical subjects
- general knowledge

Keep answers short and actionable unless the user asks for detail.
Do not unnecessarily repeat the user's question.
"""


# ============================================================
# JARVIS BRAIN
# ============================================================

class JarvisBrain:
    """
    Main AI brain of JARVIS.

    Responsibilities:

        1. Gemini communication
        2. Model fallback
        3. Conversation memory
        4. Local command processing
        5. Text-to-speech
        6. Voice selection
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None
    ):

        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        self.api_key = (
            api_key
            or Config.GEMINI_API_KEY
        )

        # ----------------------------------------------------
        # PRIMARY MODEL
        # ----------------------------------------------------

        primary_model = (
            model
            or Config.GEMINI_MODEL
        )

        # ----------------------------------------------------
        # BUILD MODEL FALLBACK CHAIN
        # ----------------------------------------------------
        #
        # Example:
        #
        # gemini-3.1-flash-lite
        #       ↓
        # gemini-3.5-flash
        #       ↓
        # gemini-3.5-flash-lite
        #       ↓
        # gemini-2.5-flash
        #
        # ----------------------------------------------------

        self.models = []

        if primary_model:
            self.models.append(
                primary_model
            )

        for fallback_model in getattr(
            Config,
            "GEMINI_FALLBACK_MODELS",
            []
        ):

            if (
                fallback_model
                and fallback_model not in self.models
            ):
                self.models.append(
                    fallback_model
                )

        # ----------------------------------------------------
        # Maximum model attempts
        # ----------------------------------------------------

        max_attempts = getattr(
            Config,
            "GEMINI_MAX_MODEL_ATTEMPTS",
            len(self.models)
        )

        self.models = self.models[
            :max_attempts
        ]

        # ----------------------------------------------------
        # Current model
        # ----------------------------------------------------

        self.current_model = (
            self.models[0]
            if self.models
            else None
        )

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        self.memory = Memory()

        # ----------------------------------------------------
        # GEMINI CLIENT
        # ----------------------------------------------------

        if not self.api_key:

            logger.warning(
                "GEMINI_API_KEY is not set - "
                "brain will run in offline/echo mode."
            )

            self.client = None

        else:

            try:

                self.client = g.Client(
                    api_key=self.api_key
                )

                logger.info(
                    "Gemini client initialized."
                )

                logger.info(
                    "Model fallback chain: %s",
                    ", ".join(self.models)
                )

            except Exception:

                logger.exception(
                    "Failed to initialize Gemini client."
                )

                self.client = None

        # ----------------------------------------------------
        # TEXT-TO-SPEECH
        # ----------------------------------------------------

        self.tts_engine = None

        self.voice_gender = getattr(
            Config,
            "JARVIS_VOICE_GENDER",
            "female"
        )

        self.voice_rate = getattr(
            Config,
            "JARVIS_VOICE_RATE",
            175
        )

        self.voice_volume = getattr(
            Config,
            "JARVIS_VOICE_VOLUME",
            1.0
        )

        # ----------------------------------------------------
        # Initialize TTS
        # ----------------------------------------------------

        self._initialize_tts()

    # ========================================================
    # INITIALIZE TTS
    # ========================================================

    def _initialize_tts(self):

        if pyttsx3 is None:

            logger.warning(
                "pyttsx3 is not installed. "
                "Voice output is disabled."
            )

            return

        try:

            self.tts_engine = pyttsx3.init()

            # Speech speed
            self.tts_engine.setProperty(
                "rate",
                self.voice_rate
            )

            # Volume
            self.tts_engine.setProperty(
                "volume",
                self.voice_volume
            )

            # Select configured voice
            self.set_voice(
                self.voice_gender
            )

            logger.info(
                "JARVIS TTS initialized."
            )

        except Exception:

            logger.exception(
                "Failed to initialize TTS."
            )

            self.tts_engine = None

    # ========================================================
    # STOP COMMAND CHECK
    # ========================================================

    def is_stop_command(
        self,
        prompt: str
    ) -> bool:
        """
        Determine whether a message is a local stop command.

        This function does NOT contact Gemini.
        """

        if not prompt:
            return False

        command = (
            prompt
            .lower()
            .strip()
        )

        stop_commands = getattr(
            Config,
            "STOP_COMMANDS",
            {
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
        )

        return command in stop_commands

    # ========================================================
    # STOP SPEAKING
    # ========================================================

    def stop_speaking(self) -> str:
        """
        Immediately stop JARVIS speech.

        No Gemini API request is made.
        """

        if not self.tts_engine:
            return ""

        try:

            self.tts_engine.stop()

            logger.info(
                "JARVIS speech stopped."
            )

        except Exception:

            logger.exception(
                "Unable to stop JARVIS speech."
            )

        return ""

    # ========================================================
    # SPEAK
    # ========================================================

    def speak(
        self,
        text: str
    ):

        """
        Speak text using pyttsx3.
        """

        if not text:
            return

        if not self.tts_engine:

            logger.warning(
                "TTS engine is unavailable."
            )

            return

        try:

            self.tts_engine.say(
                text
            )

            self.tts_engine.runAndWait()

        except Exception:

            logger.exception(
                "JARVIS speech failed."
            )

    # ========================================================
    # LIST VOICES
    # ========================================================

    def list_voices(self):
        """
        Return all voices installed on the system.
        """

        if not self.tts_engine:
            return []

        try:

            voices = (
                self.tts_engine
                .getProperty("voices")
            )

            result = []

            for index, voice in enumerate(
                voices
            ):

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
                    ),
                    "languages": getattr(
                        voice,
                        "languages",
                        []
                    )
                })

            return result

        except Exception:

            logger.exception(
                "Unable to list voices."
            )

            return []

    # ========================================================
    # SET VOICE
    # ========================================================

    def set_voice(
        self,
        gender: str = "female"
    ) -> bool:
        """
        Select a male or female voice.

        Example:

            brain.set_voice("male")
            brain.set_voice("female")
        """

        if not self.tts_engine:
            return False

        gender = (
            gender
            .lower()
            .strip()
        )

        if gender not in {
            "male",
            "female"
        }:

            logger.warning(
                "Invalid voice gender: %s",
                gender
            )

            return False

        try:

            voices = (
                self.tts_engine
                .getProperty("voices")
            )

            if not voices:
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

            selected_voice = None

            # ------------------------------------------------
            # Search installed voices
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

                combined = (
                    voice_id
                    + " "
                    + voice_name
                    + " "
                    + voice_gender
                )

                if any(
                    keyword in combined
                    for keyword in keywords
                ):

                    selected_voice = voice
                    break

            # ------------------------------------------------
            # Fallback
            # ------------------------------------------------

            if selected_voice is None:

                if gender == "female":

                    selected_voice = voices[0]

                elif len(voices) > 1:

                    selected_voice = voices[1]

                else:

                    selected_voice = voices[0]

            # ------------------------------------------------
            # Apply voice
            # ------------------------------------------------

            self.tts_engine.setProperty(
                "voice",
                selected_voice.id
            )

            self.voice_gender = gender

            logger.info(
                "Selected %s voice: %s",
                gender,
                getattr(
                    selected_voice,
                    "name",
                    selected_voice.id
                )
            )

            return True

        except Exception:

            logger.exception(
                "Unable to set %s voice.",
                gender
            )

            return False

    # ========================================================
    # SET VOICE RATE
    # ========================================================

    def set_voice_rate(
        self,
        rate: int
    ) -> bool:

        if not self.tts_engine:
            return False

        try:

            self.tts_engine.setProperty(
                "rate",
                rate
            )

            self.voice_rate = rate

            return True

        except Exception:

            logger.exception(
                "Unable to change voice rate."
            )

            return False

    # ========================================================
    # SET VOICE VOLUME
    # ========================================================

    def set_voice_volume(
        self,
        volume: float
    ) -> bool:

        if not self.tts_engine:
            return False

        try:

            volume = max(
                0.0,
                min(1.0, volume)
            )

            self.tts_engine.setProperty(
                "volume",
                volume
            )

            self.voice_volume = volume

            return True

        except Exception:

            logger.exception(
                "Unable to change voice volume."
            )

            return False

    # ========================================================
    # FALLBACK ERROR DETECTION
    # ========================================================

    @staticmethod
    def is_fallback_error(
        error: str
    ) -> bool:
        """
        Determine whether another Gemini model should
        be attempted.
        """

        error_upper = error.upper()

        fallback_errors = [
            "429",
            "RESOURCE_EXHAUSTED",
            "QUOTA",
            "RATE LIMIT",
            "RATE_LIMIT",
            "404",
            "NOT_FOUND",
            "MODEL NOT FOUND",
            "MODEL IS NOT FOUND",
            "MODEL_NOT_FOUND",
        ]

        return any(
            item in error_upper
            for item in fallback_errors
        )

    # ========================================================
    # GENERATE CONTENT
    # ========================================================

    def _generate(
        self,
        prompt: str
    ) -> str:
        """
        Generate Gemini response.

        If a model fails due to quota or availability,
        the next configured model is automatically tried.
        """

        if not self.client:

            return (
                "[offline mode] "
                "GEMINI_API_KEY is not configured."
            )

        if not self.models:

            return (
                "No Gemini models are configured."
            )

        last_error = None

        # ----------------------------------------------------
        # Try models sequentially
        # ----------------------------------------------------

        for index, model in enumerate(
            self.models
        ):

            try:

                logger.info(
                    "Trying Gemini model: %s",
                    model
                )

                response = (
                    self.client
                    .models
                    .generate_content(
                        model=model,
                        contents=prompt
                    )
                )

                # --------------------------------------------
                # Successful model
                # --------------------------------------------

                self.current_model = model

                logger.info(
                    "Gemini response received "
                    "from model: %s",
                    model
                )

                if response.text:

                    return response.text

                return (
                    "I received an empty response "
                    "from the AI model."
                )

            except Exception as exc:

                error = str(exc)

                last_error = error

                # --------------------------------------------
                # Quota / model unavailable
                # --------------------------------------------

                if self.is_fallback_error(
                    error
                ):

                    logger.warning(
                        "Gemini model '%s' failed "
                        "with quota/availability error.",
                        model
                    )

                    if (
                        index
                        < len(self.models) - 1
                    ):

                        next_model = (
                            self.models[index + 1]
                        )

                        logger.info(
                            "Switching from '%s' "
                            "to '%s'.",
                            model,
                            next_model
                        )

                        continue

                    # ----------------------------------------
                    # All models exhausted
                    # ----------------------------------------

                    logger.warning(
                        "All configured Gemini "
                        "models failed."
                    )

                    return (
                        "I'm temporarily unable to "
                        "contact my AI models. "
                        "The configured models may have "
                        "reached their quota or may be "
                        "temporarily unavailable."
                    )

                # --------------------------------------------
                # Other error
                # --------------------------------------------

                logger.exception(
                    "Gemini model '%s' failed.",
                    model
                )

                return (
                    "Sorry, I ran into an error "
                    "talking to the model."
                )

        return (
            "Sorry, all configured AI models failed. "
            f"Last error: {last_error}"
        )

    # ========================================================
    # ASK
    # ========================================================

    def ask(
        self,
        prompt: str,
        session_id: str = "default"
    ) -> str:
        """
        Main JARVIS AI function.

        IMPORTANT:

            STOP COMMAND
                  ↓
            local handling
                  ↓
            NO GEMINI REQUEST

        Example:

            brain.ask("Jarvis stop")

        immediately stops speech.
        """

        if not prompt:
            return ""

        # ====================================================
        # PRIORITY 1
        # LOCAL STOP COMMAND
        # ====================================================
        #
        # This happens BEFORE:
        #
        #     memory
        #     Gemini
        #     model fallback
        #
        # ====================================================

        if self.is_stop_command(
            prompt
        ):

            logger.info(
                "Local stop command detected: %s",
                prompt
            )

            self.stop_speaking()

            return ""

        # ====================================================
        # MEMORY
        # ====================================================

        history = self.memory.get_recent(
            session_id,
            limit=10
        )

        context_block = ""

        if history:

            context_block = "\n".join(
                f"{'User' if role == 'user' else 'JARVIS'}: {text}"
                for role, text in history
            )

            context_block = (
                "\nRecent conversation:\n"
                + context_block
                + "\n"
            )

        # ====================================================
        # FULL PROMPT
        # ====================================================

        full_prompt = (
            SYSTEM_PERSONA
            + "\n"
            + context_block
            + "\nUser: "
            + prompt
            + "\nJARVIS:"
        )

        # ====================================================
        # OFFLINE MODE
        # ====================================================

        if not self.client:

            reply = (
                f"[offline mode] "
                f"I heard: '{prompt}'. "
                f"Set GEMINI_API_KEY to enable "
                f"real answers."
            )

        # ====================================================
        # GEMINI
        # ====================================================

        else:

            reply = self._generate(
                full_prompt
            )

        # ====================================================
        # SAVE MEMORY
        # ====================================================

        self.memory.add(
            session_id,
            "user",
            prompt
        )

        self.memory.add(
            session_id,
            "assistant",
            reply
        )

        return reply

    # ========================================================
    # QUICK
    # ========================================================

    def quick(
        self,
        prompt: str
    ) -> str:
        """
        One-off generation without conversation memory.

        Model fallback is still enabled.
        """

        # ----------------------------------------------------
        # STOP MUST REMAIN LOCAL
        # ----------------------------------------------------

        if self.is_stop_command(
            prompt
        ):

            self.stop_speaking()

            return ""

        return self._generate(
            prompt
        )

    # ========================================================
    # STATUS
    # ========================================================

    def status(self) -> dict:
        """
        Return current JARVIS status.
        """

        return {
            "gemini_available": (
                self.client is not None
            ),

            "configured_models": (
                self.models
            ),

            "current_model": (
                self.current_model
            ),

            "voice_available": (
                self.tts_engine is not None
            ),

            "voice_gender": (
                self.voice_gender
            ),

            "voice_rate": (
                self.voice_rate
            ),

            "voice_volume": (
                self.voice_volume
            ),
        }