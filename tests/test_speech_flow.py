"""Regression checks for speech capture, worker startup, and message routing."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest

import numpy as np

from src.stt.whisper_stt import BLOCK_SIZE, WhisperSTT


ROOT = Path(__file__).resolve().parents[1]


class WhisperWorkerTests(unittest.TestCase):
    def test_application_worker_dispatch_uses_pipe_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_module = Path(temp_dir) / "faster_whisper.py"
            fake_module.write_text(
                "from types import SimpleNamespace\n"
                "class WhisperModel:\n"
                "    def __init__(self, *args, **kwargs):\n"
                "        self.hf_tokenizer = SimpleNamespace(encode=lambda *a, **k: [])\n"
                "    def transcribe(self, audio, **kwargs):\n"
                "        return [SimpleNamespace(text='hello world')], None\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PYTHONPATH"] = os.pathsep.join((temp_dir, str(ROOT)))
            audio = np.zeros(BLOCK_SIZE, dtype=np.float32).tobytes()
            header = json.dumps(
                {"type": "transcribe", "language": "en", "size": len(audio)}
            ).encode() + b"\n"

            result = subprocess.run(
                [sys.executable, str(ROOT / "main.py"), "--whisper-worker",
                 "unused-model", "cpu", "0", "[]"],
                input=header + audio,
                capture_output=True,
                env=env,
                timeout=15,
                check=True,
            )
            messages = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(messages[0]["status"], "loaded")
            self.assertEqual(messages[1], {"type": "result", "text": "hello world"})


class CaptureLoopTests(unittest.TestCase):
    def test_stop_does_not_block_when_audio_queue_is_full(self) -> None:
        engine = WhisperSTT()
        frame = np.zeros((BLOCK_SIZE, 1), dtype=np.int16)
        for _ in range(engine._audio_queue.maxsize):
            engine._audio_queue.put_nowait(frame)

        stop_thread = threading.Thread(target=engine.stop_listening, daemon=True)
        stop_thread.start()
        stop_thread.join(timeout=1)

        self.assertFalse(stop_thread.is_alive(), "Stopping a full queue blocked")
        self.assertTrue(engine._stop_event.is_set())
        self.assertTrue(engine._audio_queue.full())

    def test_continuous_speech_respects_recording_limit(self) -> None:
        engine = WhisperSTT(max_record_seconds=0.09)
        engine._vad_check = lambda vad, data: True
        transcribed_lengths = []
        engine._transcribe = lambda frames, language: transcribed_lengths.append(len(frames))
        frame = np.zeros((BLOCK_SIZE, 1), dtype=np.int16)
        for _ in range(4):
            engine._audio_queue.put_nowait(frame)
        engine._audio_queue.put_nowait(None)

        engine._loop_vad(None, "en")

        self.assertEqual(transcribed_lengths, [3])


class GuiRoutingTests(unittest.TestCase):
    def test_manual_send_bypasses_live_transcript_accumulator(self) -> None:
        from src.config.settings import AppSettings
        from src.gui.main_window import MainWindow

        sent = []
        displayed = []
        settings = AppSettings(ptt_live_transcribe=True, tts_enabled=False)
        window = SimpleNamespace(
            settings=settings,
            _transcript=SimpleNamespace(appendPlainText=displayed.append),
            _osc=SimpleNamespace(send_chatbox=lambda *args, **kwargs: sent.append((args, kwargs))),
            _last_transcription="",
            _listening_status=lambda: ("Idle", "gray"),
            _set_status=lambda *args: None,
        )

        MainWindow._on_result(window, "typed message", True, manual=True)

        self.assertEqual(displayed, ["typed message"])
        self.assertEqual(sent[0][0], ("typed message",))
        self.assertEqual(window._last_transcription, "typed message")


if __name__ == "__main__":
    unittest.main()
