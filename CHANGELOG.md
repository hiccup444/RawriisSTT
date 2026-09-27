# Changelog

## 1.0.3

- Run the bundled Whisper worker from the application executable, without requiring a separate Python installation.
- Replace the original WebRTC VAD package with `webrtcvad-wheels` so voice activity detection works on current Python versions.
- Keep Stop responsive when capture queues are full or cloud recognition is shutting down.
- Enforce the maximum recording length during continuous speech.
- Route keyboard push-to-talk events through the GUI thread and preserve pending live transcripts when stopping or starting another recording.
- Send manually typed messages immediately even when live transcription is enabled.
- Avoid logging transcribed or typed message contents.
- Label Google Web Speech as a cloud service and fix release links in the documentation.
- Avoid incompatible optional PyTorch and duplicate Visual C++ runtime DLLs in the Windows bundle.
