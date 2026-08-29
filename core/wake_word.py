"""
core/wake_word.py
=======================================================
Wake word detection - "Hey Jarvis"
=======================================================
Two strategies are provided:

1. `PorcupineWakeWord` - real-time, always-listening wake word
   detection using Picovoice Porcupine (offline, low CPU). Requires
   PORCUPINE_ACCESS_KEY and a custom "jarvis" .ppn keyword file.

2. `SimpleTextWakeWord` - a lightweight fallback that just checks
   whether a transcribed phrase *starts with* the wake word. Useful
   when running STT on short audio clips instead of a live stream.
"""

from config import Config
from utils.helpers import strip_wake_word
from utils.logger import get_logger

logger = get_logger("jarvis.wake_word")


class SimpleTextWakeWord:
    def __init__(self, wake_word: str | None = None):
        self.wake_word = (wake_word or Config.WAKE_WORD).lower()

    def detected(self, text: str) -> bool:
        return text.strip().lower().startswith(("hey " + self.wake_word, self.wake_word))

    def strip(self, text: str) -> str:
        return strip_wake_word(text, self.wake_word)


class PorcupineWakeWord:
    """Continuous microphone wake-word listener (desktop/edge device use)."""

    def __init__(self, keyword_paths=None, on_wake=None):
        self.on_wake = on_wake
        try:
            import pvporcupine
            import pyaudio
            self.pvporcupine = pvporcupine
            self.pyaudio = pyaudio
            self.porcupine = pvporcupine.create(
                access_key=Config.PORCUPINE_ACCESS_KEY,
                keyword_paths=keyword_paths,
                keywords=None if keyword_paths else ["jarvis"],
            )
            self.available = True
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Porcupine wake-word engine unavailable: {exc}")
            self.available = False

    def listen_forever(self):
        """Blocking loop - run this in a background thread."""
        if not self.available:
            logger.warning("Wake word engine not available; skipping listen loop.")
            return

        pa = self.pyaudio.PyAudio()
        stream = pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=self.pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
        )
        logger.info("Wake-word listener started ('Hey Jarvis')...")
        try:
            while True:
                pcm = stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                import struct
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                result = self.porcupine.process(pcm)
                if result >= 0 and self.on_wake:
                    self.on_wake()
        finally:
            stream.close()
            pa.terminate()
            self.porcupine.delete()
