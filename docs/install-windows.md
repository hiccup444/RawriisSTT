# Windows Setup

## Requirements

- Windows 10 or 11
- VRChat with OSC enabled
- A microphone

A CUDA-capable NVIDIA GPU is optional but recommended if you plan to use Whisper - it significantly speeds up transcription. CPU-only works fine.

---

## Installation

1. Go to the [Releases page](https://github.com/hiccup444/RawriisSST/releases/latest) and download the latest `RawriisSTT-vX.X.X.zip`.
2. Extract the zip to any folder (e.g. `C:\Programs\RawriisSTT\`).
3. Run `RawriisSTT.exe`.

No installation wizard, no Python required - everything is bundled.

---

## Enable VRChat OSC

RawriisSTT sends text to VRChat over OSC. You need to enable it once inside VRChat:

1. Open the VRChat radial menu.
2. Go to **Options → OSC → Enable**.

OSC stays enabled between sessions.

---

## First-Time Setup (Whisper - Recommended)

1. Open **Settings** (top-right of the main window).
2. Go to the **Speech-to-Text** tab.
3. Under **Whisper Models**, find `base` and click **Download**. Wait for it to finish.
4. Close Settings.
5. On the main window:
   - Select your **microphone** from the dropdown.
   - Set your **language** (or leave it on Auto).
   - Make sure **Whisper** is selected as the engine.
6. Click **Launch Whisper** and wait for the model to load (first load takes a few seconds).
7. Enable the **Chatbox** toggle so transcriptions are sent to VRChat.
8. Click **Start Recording**.

Speak - your words will appear in the VRChat chatbox.

---

## GPU Acceleration (Optional)

By default, Whisper runs on CPU. To enable CUDA:

1. Install the [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) matching your driver.
2. Open a command prompt in the RawriisSTT folder and run:
   ```
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```
3. In **Settings → Speech-to-Text**, set **Whisper Device** to `cuda`.

---

## Presets

If you switch between different setups (e.g. different games, languages, or TTS voices), use **Presets** on the main window to save and restore your full configuration instantly.

---

## Troubleshooting

**Nothing appears in the VRChat chatbox**
- Check that OSC is enabled in VRChat (Options → OSC → Enable).
- Make sure the OSC port in Settings → General matches VRChat's port (default: 9000).

**Whisper says "no model downloaded"**
- Go to Settings → Speech-to-Text and download a model before clicking Launch Whisper.

**Microphone not listed**
- Make sure Windows has microphone access enabled (Settings → Privacy → Microphone).
- Try unplugging and replugging the device, then restarting the app.

**App won't open / crashes immediately**
- Make sure you extracted the full zip - don't run the exe directly from inside the zip.
- Some antivirus software flags PyInstaller executables as false positives; add an exception if needed.
