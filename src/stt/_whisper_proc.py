"""Standalone subprocess worker for faster-whisper.

Launched by WhisperSTT.load_model() via subprocess.Popen.
Protocol (all I/O in binary mode, newline-delimited JSON headers):

  Parent → child:
    {"type": "transcribe", "language": "en", "size": <bytes>}\n
    <raw float32 audio bytes>

  Child → parent:
    {"status": "loaded"}\n                      -- on startup
    {"status": "error", "message": "..."}\n     -- on startup failure
    {"type": "result", "text": "..."}\n         -- after each transcription
"""

import json
import sys


def main() -> None:
    if len(sys.argv) < 3:
        _send({"status": "error", "message": "Usage: _whisper_proc.py <model_path> <device>"})
        sys.exit(1)

    model_path, device = sys.argv[1], sys.argv[2]

    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_path, device=device, compute_type="float32")
        _send({"status": "loaded"})
    except Exception as exc:
        _send({"status": "error", "message": str(exc)})
        sys.exit(1)

    import numpy as np
    stdin = sys.stdin.buffer

    while True:
        header_line = stdin.readline()
        if not header_line:
            break

        try:
            header = json.loads(header_line.strip())
        except Exception:
            continue

        if header.get("type") == "transcribe":
            size = int(header.get("size", 0))
            language = header.get("language", "en")

            # Read exactly `size` bytes of float32 audio
            audio_bytes = b""
            remaining = size
            while remaining > 0:
                chunk = stdin.read(remaining)
                if not chunk:
                    break
                audio_bytes += chunk
                remaining -= len(chunk)

            try:
                audio = np.frombuffer(audio_bytes, dtype=np.float32)
                segments, _ = model.transcribe(
                    audio,
                    language=language if language != "auto" else None,
                    beam_size=5,
                    vad_filter=False,
                )
                text = " ".join(seg.text.strip() for seg in segments).strip()
                _send({"type": "result", "text": text})
            except Exception:
                _send({"type": "result", "text": ""})

        elif header.get("type") == "quit":
            break


def _send(obj: dict) -> None:
    sys.stdout.buffer.write(json.dumps(obj).encode() + b"\n")
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
