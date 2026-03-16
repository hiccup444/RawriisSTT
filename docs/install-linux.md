# Linux Setup

RawriisSTT runs from source on Linux. There is no pre-built Linux binary - use the launcher script instead.

---

## Requirements

- Python 3.10 or newer
- `pip`
- PortAudio (required by PyAudio)
- VRChat running via Steam/Proton with OSC enabled

---

## System Dependencies

Most packages install automatically via `launcher.py`. However, **PyAudio must be installed from your distro's package manager** on Linux — the pip version links against a different PortAudio build than sounddevice, which causes a crash at runtime. This only affects the **System Speech** and **Vosk** engines; Whisper and Azure work without it.

**Debian / Ubuntu / Mint:**
```bash
sudo apt install python3-pyaudio
```

**Arch / Manjaro:**
```bash
sudo pacman -S python-pyaudio
```

**Fedora:**
```bash
sudo dnf install python3-pyaudio
```

If you only plan to use Whisper (recommended), you can skip the above entirely.

---

## Running the App

```bash
git clone https://github.com/hiccup444/RawriisSST.git
cd RawriisSTT
python3 launcher.py
```

`launcher.py` checks for missing packages and installs them automatically on first run. Subsequent launches skip straight to the app.

If you prefer to install manually:
```bash
pip install -r requirements.txt
python3 main.py
```

---

## Enable VRChat OSC

VRChat running under Proton does not auto-detect OSC on Linux. Enable it manually:

1. Open the VRChat radial menu.
2. Go to **Options → OSC → Enable**.

Alternatively, add `--enable-sdk-log-levels` to VRChat's launch options in Steam to confirm OSC traffic in the log.

---

## First-Time Setup (Whisper - Recommended)

1. Launch the app with `python3 launcher.py`.
2. Open **Settings → Speech-to-Text**.
3. Download a Whisper model (e.g. `base`) from the model list.
4. Close Settings.
5. On the main window:
   - Select your **microphone**.
   - Set your **language** (or leave on Auto).
   - Confirm **Whisper** is selected.
   - Make sure the **Chatbox** toggle is enabled so transcriptions are sent to VRChat.
6. Click **Launch Whisper**, then **Start Recording**.

---

## GPU Acceleration (Optional)

To run Whisper on an NVIDIA GPU:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Then set **Whisper Device** to `cuda` in Settings → Speech-to-Text.

For AMD GPU support via ROCm, follow the [PyTorch ROCm install guide](https://pytorch.org/get-started/locally/).

---

## VAD & webrtcvad Notes

`webrtcvad` requires a C compiler to build on Linux. If the install fails:

```bash
sudo apt install build-essential  # Debian/Ubuntu
sudo pacman -S base-devel         # Arch
```

Then retry: `pip install webrtcvad`

---

## SteamVR Bindings on Linux

SteamVR runs natively on Linux via Steam. RawriisSTT will detect it automatically. Controller binding setup is the same as on Windows - see [SteamVR Bindings](steamvr.md).

---

## Troubleshooting

**All packages fail to install on Ubuntu 24.04 (`error: externally-managed-environment`)**
- Ubuntu 24.04 blocks pip from installing into the system Python by default. The launcher detects this automatically and retries with `--break-system-packages`. If you installed pip manually or are using a non-standard setup, run:
  ```bash
  pip install --break-system-packages -r requirements.txt
  ```
- Alternatively, use a virtual environment:
  ```bash
  python3 -m venv venv && source venv/bin/activate
  python3 launcher.py
  ```

**`ModuleNotFoundError: No module named 'faster_whisper'` when launching Whisper**
- This means the Whisper subprocess launched a different Python interpreter than the one with your packages installed. Run the app via `python3 launcher.py` (not `python3 main.py`) to ensure packages are installed into and used from the same interpreter.

**System Speech crashes with `malloc(): unsorted double linked list corrupted`**
- This is caused by pip-installed PyAudio conflicting with sounddevice's bundled PortAudio. Install PyAudio from your package manager instead (see System Dependencies above) and do not `pip install PyAudio`.

**`No module named 'PyAudio'` during install**
- Install PyAudio from your package manager (see System Dependencies above). Do not use pip for PyAudio on Linux.

**Keyboard PTT hotkey doesn't work / "requires read access to /dev/input"**
- Add your user to the `input` group, then log out and back in:
  ```bash
  sudo usermod -aG input $USER
  ```
- Alternatively, use SteamVR controller bindings for PTT instead of a keyboard hotkey.

**Microphone not detected**
- Check PipeWire/PulseAudio is running: `pactl info`
- List available devices: `python3 -c "import sounddevice; print(sounddevice.query_devices())"`

**Nothing appears in VRChat chatbox**
- Confirm OSC is enabled inside VRChat.
- VRChat listens on `127.0.0.1:9000` by default - check Settings → General matches.
