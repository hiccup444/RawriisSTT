from __future__ import annotations

import json
import logging
import queue
import threading
from typing import Optional

from .base import ResultCallback, STTEngine, STTResult

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 4000  # 250ms at 16kHz


class VoskSTT(STTEngine):
    """Offline speech-to-text using the Vosk library."""

    def __init__(self, model_path: str) -> None:
        super().__init__()
        self._model_path = model_path
        self._model = None   # pre-loaded vosk.Model (optional)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._audio_queue: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=20)

    @property
    def name(self) -> str:
        return "Vosk (offline)"

    @property
    def requires_model_download(self) -> bool:
        return True

    @property
    def is_model_loaded(self) -> bool:
        return self._model is not None

    def load_model(self) -> None:
        """Load the Vosk model into memory. Blocking — call from a background thread."""
        if self._model is not None:
            return
        if not self._model_path:
            raise ValueError("Vosk model path is not configured.")
        from vosk import Model
        logger.info("Loading Vosk model from %s…", self._model_path)
        self._model = Model(self._model_path)
        logger.info("Vosk model loaded.")

    def unload_model(self) -> None:
        self._model = None
        logger.info("Vosk model unloaded.")

    def start_listening(
        self,
        callback: ResultCallback,
        device_index: Optional[int] = None,
        language: str = "en",
    ) -> None:
        if self._listening:
            return
        if not self._model_path:
            raise ValueError("Vosk model path is not configured.")

        self._callback = callback
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._capture_loop,
            args=(device_index,),
            daemon=True,
            name="VoskSTT",
        )
        self._listening = True
        self._thread.start()
        self._thread.join()  # Block the QThread until capture finishes

    def stop_listening(self) -> None:
        self._stop_event.set()
        self._audio_queue.put(None)
        if self._thread:
            self._thread.join(timeout=5)
        self._listening = False

    def _capture_loop(self, device_index: Optional[int]) -> None:
        try:
            import pyaudio
            from vosk import KaldiRecognizer, Model

            model = self._model if self._model is not None else Model(self._model_path)
            recognizer = KaldiRecognizer(model, SAMPLE_RATE)

            pa = pyaudio.PyAudio()
            kwargs = dict(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SAMPLES,
            )
            if device_index is not None:
                kwargs["input_device_index"] = device_index

            stream = pa.open(**kwargs)
            stream.start_stream()

            try:
                while not self._stop_event.is_set():
                    data = stream.read(CHUNK_SAMPLES, exception_on_overflow=False)
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()
                        if text and self._callback:
                            self._callback(STTResult(text=text, is_final=True))
                    else:
                        partial = json.loads(recognizer.PartialResult())
                        partial_text = partial.get("partial", "").strip()
                        if partial_text and self._callback:
                            self._callback(STTResult(text=partial_text, is_final=False))
            finally:
                stream.stop_stream()
                stream.close()
                pa.terminate()
        except Exception as exc:
            logger.exception("VoskSTT error: %s", exc)
        finally:
            self._listening = False
