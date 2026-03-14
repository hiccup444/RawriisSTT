from __future__ import annotations

import logging
import threading
from typing import Optional

from .base import ResultCallback, STTEngine, STTResult

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
BLOCK_SIZE = 480  # 30 ms at 16 kHz

# Map simple language codes to Azure BCP-47 locale strings
AZURE_LANGUAGE_MAP: dict[str, str] = {
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
    "pt": "pt-BR",
    "nl": "nl-NL",
    "ru": "ru-RU",
    "zh": "zh-CN",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "ar": "ar-SA",
    "hi": "hi-IN",
    "pl": "pl-PL",
    "sv": "sv-SE",
    "da": "da-DK",
    "fi": "fi-FI",
    "nb": "nb-NO",
    "tr": "tr-TR",
    "cs": "cs-CZ",
    "sk": "sk-SK",
    "hu": "hu-HU",
    "ro": "ro-RO",
    "uk": "uk-UA",
    "id": "id-ID",
    "ms": "ms-MY",
    "th": "th-TH",
    "vi": "vi-VN",
}


class AzureSTT(STTEngine):
    """Speech-to-text using Microsoft Azure Cognitive Services Speech SDK.

    Audio is captured via sounddevice so the selected microphone device is
    respected.  Frames are pushed to an Azure PushAudioInputStream which allows
    us to route any PortAudio device into the Azure recognizer.

    Both interim (is_final=False) and final (is_final=True) results are emitted
    via the callback so that the live-transcribe accumulator in the GUI works the
    same as it does for Whisper.
    """

    def __init__(self, subscription_key: str, region: str) -> None:
        super().__init__()
        self._key = subscription_key
        self._region = region
        self._recognizer = None
        self._push_stream = None
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def name(self) -> str:
        return "Azure Speech"

    def start_listening(
        self,
        callback: ResultCallback,
        device_index: Optional[int] = None,
        language: str = "en",
    ) -> None:
        if self._listening:
            return
        if not self._key or not self._region:
            raise ValueError("Azure subscription key and region are required.")

        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as exc:
            raise ImportError("azure-cognitiveservices-speech is not installed.") from exc

        if language == "auto":
            # Azure doesn't support open-ended auto-detect without specifying candidate locales.
            # Fall back to en-US; users should pick an explicit language when using Azure.
            locale = "en-US"
        else:
            locale = AZURE_LANGUAGE_MAP.get(language, language)
        speech_config = speechsdk.SpeechConfig(subscription=self._key, region=self._region)
        speech_config.speech_recognition_language = locale

        # Use a PushAudioInputStream so we can feed audio from any PortAudio device
        stream_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=SAMPLE_RATE,
            bits_per_sample=16,
            channels=1,
        )
        self._push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
        audio_config = speechsdk.audio.AudioConfig(stream=self._push_stream)

        self._recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        self._callback = callback
        self._stop_event.clear()

        self._recognizer.recognizing.connect(self._on_recognizing)
        self._recognizer.recognized.connect(self._on_recognized)
        self._recognizer.session_stopped.connect(lambda _: logger.info("Azure session stopped."))
        self._recognizer.canceled.connect(lambda evt: logger.warning("Azure canceled: %s", evt))

        self._recognizer.start_continuous_recognition_async()
        self._listening = True
        logger.info("Azure STT started (locale=%s, device=%s)", locale, device_index)

        # Capture audio in a background thread and push it to Azure
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(device_index,),
            daemon=True,
            name="AzureSTTCapture",
        )
        self._capture_thread.start()
        # Block the calling QThread so results continue to be delivered
        self._capture_thread.join()

    def _capture_loop(self, device_index: Optional[int]) -> None:
        """Capture audio from the selected device and push frames to Azure."""
        try:
            import sounddevice as sd

            def audio_callback(indata, frames: int, time_info, status) -> None:
                if status:
                    logger.debug("sounddevice status: %s", status)
                if not self._stop_event.is_set() and self._push_stream is not None:
                    self._push_stream.write(indata.tobytes())

            kwargs = dict(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=BLOCK_SIZE,
                callback=audio_callback,
            )
            if device_index is not None:
                kwargs["device"] = device_index

            with sd.InputStream(**kwargs):
                self._stop_event.wait()  # Block until stop_listening() is called

        except Exception as exc:
            logger.exception("AzureSTT capture error: %s", exc)
        finally:
            # Close the push stream — Azure sees end-of-audio and finishes recognition
            if self._push_stream is not None:
                try:
                    self._push_stream.close()
                except Exception:
                    pass
            self._listening = False

    def _on_recognizing(self, evt) -> None:
        """Fired continuously while Azure is recognizing (interim/partial result)."""
        try:
            import azure.cognitiveservices.speech as speechsdk
            if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                text = evt.result.text.strip()
                if text and self._callback:
                    self._callback(STTResult(text=text, is_final=False))
        except Exception as exc:
            logger.debug("AzureSTT _on_recognizing error: %s", exc)

    def _on_recognized(self, evt) -> None:
        """Fired when Azure commits a final recognition result."""
        try:
            import azure.cognitiveservices.speech as speechsdk
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text.strip()
                if text and self._callback:
                    self._callback(STTResult(text=text, is_final=True))
        except Exception as exc:
            logger.debug("AzureSTT _on_recognized error: %s", exc)

    def stop_listening(self) -> None:
        self._stop_event.set()
        if self._capture_thread:
            self._capture_thread.join(timeout=3)
            self._capture_thread = None
        if self._recognizer:
            try:
                self._recognizer.stop_continuous_recognition_async().get()
            except Exception as exc:
                logger.warning("Azure stop error: %s", exc)
            self._recognizer = None
        self._push_stream = None
        self._listening = False
        logger.info("Azure STT stopped.")
