from __future__ import annotations

import logging
import threading
from typing import Optional

from .base import ResultCallback, STTEngine, STTResult

logger = logging.getLogger(__name__)


def _patch_flac_encoding() -> None:
    """Replace speech_recognition's subprocess FLAC encoder with soundfile.

    In PyInstaller frozen apps running as admin, subprocess handle inheritance
    fails with [WinError 50]. soundfile provides in-process FLAC encoding that
    avoids the subprocess entirely.
    """
    try:
        import io as _io
        import speech_recognition as sr
        import soundfile as sf

        def _get_flac_data(self, convert_rate=None, convert_width=None):
            wav_data = self.get_wav_data(convert_rate, convert_width)
            with _io.BytesIO(wav_data) as wav_buf:
                data, samplerate = sf.read(wav_buf)
            flac_buf = _io.BytesIO()
            sf.write(flac_buf, data, samplerate, format="FLAC", subtype="PCM_16")
            flac_buf.seek(0)
            return flac_buf.read()

        sr.AudioData.get_flac_data = _get_flac_data
        logger.debug("FLAC encoding patched to use soundfile.")
    except ImportError as exc:
        logger.debug("Could not patch FLAC encoding (%s) — will try subprocess fallback.", exc)


class SystemSTT(STTEngine):
    """Speech-to-text using the SpeechRecognition library + Google Web Speech API.

    Uses soundfile for in-process FLAC encoding to avoid subprocess issues
    in frozen/elevated apps.
    """

    def __init__(self) -> None:
        super().__init__()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def name(self) -> str:
        return "System Speech"

    def start_listening(
        self,
        callback: ResultCallback,
        device_index: Optional[int] = None,
        language: str = "en",
    ) -> None:
        if self._listening:
            return
        self._callback = callback
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._capture_loop,
            args=(device_index, language),
            daemon=True,
            name="SystemSTT",
        )
        self._listening = True
        self._thread.start()
        self._thread.join()  # Block the QThread until capture finishes

    def stop_listening(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._listening = False

    def _capture_loop(self, device_index: Optional[int], language: str) -> None:
        _patch_flac_encoding()
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()

            mic_kwargs: dict = {}
            if device_index is not None:
                mic_kwargs["device_index"] = device_index

            while not self._stop_event.is_set():
                with sr.Microphone(**mic_kwargs) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    except sr.WaitTimeoutError:
                        continue

                try:
                    text = recognizer.recognize_google(audio, language=language)
                    text = text.strip()
                    if text and self._callback:
                        self._callback(STTResult(text=text, is_final=True))
                except sr.UnknownValueError:
                    pass  # audio not understood
                except sr.RequestError as exc:
                    logger.warning("SystemSTT recognition error: %s", exc)
        except Exception as exc:
            logger.exception("SystemSTT capture error: %s", exc)
        finally:
            self._listening = False
