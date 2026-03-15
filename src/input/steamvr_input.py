"""SteamVR Input — polls three boolean actions via OpenVR's action system.

Actions:
  /actions/main/in/push_to_talk  — forwards to the existing PTT system
  /actions/main/in/stop_tts      — immediately stops TTS audio
  /actions/main/in/repeat_tts    — re-sends the last transcription

Thread model:
  A single daemon thread handles initialization retries AND the poll loop.
  If SteamVR is not running, initialization is retried every RETRY_INTERVAL_S
  seconds without blocking the GUI.  If SteamVR shuts down while running,
  openvr.shutdown() is called and the thread re-enters the retry loop.

  All action callbacks are called from the background thread.  The caller
  (MainWindow) is responsible for marshalling them to the GUI thread via
  pyqtSignal — the same pattern used by PTTHandler.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

POLL_HZ = 30
POLL_INTERVAL = 1.0 / POLL_HZ
RETRY_INTERVAL_S = 5.0

ACTION_SET    = "/actions/main"
ACT_PTT       = "/actions/main/in/push_to_talk"
ACT_STOP_TTS  = "/actions/main/in/stop_tts"
ACT_REPEAT    = "/actions/main/in/repeat_tts"


# ──────────────────────────────────────────────────── one-time registration ──

def register_manifest(vrmanifest_path: str, action_manifest_path: str) -> None:
    """Patch the vrmanifest with the absolute action_manifest_path, then register
    with SteamVR via vrpathreg.

    SteamVR's binding editor requires an absolute action_manifest_path; relative
    paths cause "failed to load manifest" errors.  We rewrite the field in place
    on every launch so the path stays correct even if the app is moved.

    Safe to call on every launch — vrpathreg is idempotent.
    Silently skipped if vrpathreg cannot be found.
    """
    import json as _json
    mf = Path(vrmanifest_path)
    mf_dir = mf.parent

    # When frozen by PyInstaller 6+, vrmanifest is in _internal/ (mf_dir),
    # but the exe lives one level up (mf_dir.parent).  In dev mode they're the same.
    if getattr(sys, "frozen", False):
        exe_dir = mf_dir.parent
    else:
        exe_dir = mf_dir

    try:
        data = _json.loads(mf.read_text(encoding="utf-8"))
        for app in data.get("applications", []):
            app["action_manifest_path"] = action_manifest_path
            # Copy icon to the exe directory and point image_path there.
            # SteamVR has trouble loading icons from inside _internal/; placing
            # the icon next to the exe is more reliable.
            img = app.get("image_path", "")
            if img:
                src_icon = mf_dir / img if not Path(img).is_absolute() else Path(img)
                dst_icon = exe_dir / src_icon.name
                if src_icon.exists() and src_icon != dst_icon:
                    import shutil as _shutil
                    try:
                        _shutil.copy2(str(src_icon), str(dst_icon))
                        logger.debug("Copied icon to exe dir: %s", dst_icon)
                    except Exception as _ie:
                        logger.debug("Could not copy icon: %s", _ie)
                app["image_path"] = str(dst_icon if dst_icon.exists() else src_icon)
            # Make binary paths absolute so SteamVR can launch the app
            for key, name in (("binary_path_windows", "RawriisSTT.exe"),
                               ("binary_path_linux",   "RawriisSTT")):
                if key in app and not Path(app[key]).is_absolute():
                    app[key] = str(exe_dir / name)
        mf.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        logger.debug("Patched vrmanifest paths to absolute")
    except Exception as exc:
        logger.warning("Could not patch vrmanifest: %s", exc)

    vrpathreg = _find_vrpathreg()
    if not vrpathreg:
        logger.debug("vrpathreg not found — skipping manifest registration")
        return
    try:
        # Remove first to flush SteamVR's cached manifest, then re-add
        subprocess.run([vrpathreg, "removemanifest", vrmanifest_path],
                       capture_output=True, timeout=10)
        result = subprocess.run(
            [vrpathreg, "addmanifest", vrmanifest_path],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            logger.info("SteamVR manifest registered: %s", vrmanifest_path)
        else:
            logger.warning(
                "vrpathreg addmanifest returned %d: %s",
                result.returncode,
                result.stderr.decode(errors="replace").strip(),
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("vrpathreg failed: %s", exc)


def _find_vrpathreg() -> Optional[str]:
    """Return the path to the vrpathreg binary, or None if not found."""
    # 1. STEAMVR_RUNTIME environment variable
    runtime_env = os.environ.get("STEAMVR_RUNTIME")
    if runtime_env:
        candidate = Path(runtime_env) / "bin" / ("vrpathreg.exe" if sys.platform == "win32" else "vrpathreg")
        if candidate.exists():
            return str(candidate)

    # 2. Common Windows install locations
    if sys.platform == "win32":
        steam_paths = [
            Path(r"C:\Program Files (x86)\Steam\steamapps\common\SteamVR\bin\win64\vrpathreg.exe"),
            Path(r"C:\Program Files\Steam\steamapps\common\SteamVR\bin\win64\vrpathreg.exe"),
        ]
        # Also check PROGRAMFILES env
        pf = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        steam_paths.append(Path(pf) / "Steam" / "steamapps" / "common" / "SteamVR" / "bin" / "win64" / "vrpathreg.exe")
        for p in steam_paths:
            if p.exists():
                return str(p)

    # 3. Linux: check ~/.steam/steam/steamapps/common/SteamVR
    if sys.platform == "linux":
        linux_candidates = [
            Path.home() / ".steam" / "steam" / "steamapps" / "common" / "SteamVR" / "bin" / "vrpathreg.sh",
            Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common" / "SteamVR" / "bin" / "vrpathreg.sh",
        ]
        for p in linux_candidates:
            if p.exists():
                return str(p)

    # 4. Fall back to PATH
    import shutil
    return shutil.which("vrpathreg")


# ──────────────────────────────────────────────── SteamVRInputManager class ──

class SteamVRInputManager:
    """Polls SteamVR boolean actions and forwards transitions to callbacks.

    Designed to be long-lived: start() once, stop() on shutdown.
    Handles SteamVR not being available at startup or disappearing at runtime.
    """

    def __init__(
        self,
        action_manifest_path: str,
        on_ptt_press: Callable[[], None],
        on_ptt_release: Callable[[], None],
        on_stop_tts: Callable[[], None],
        on_repeat_tts: Callable[[], None],
        ptt_mode: str,
    ) -> None:
        self._action_manifest = action_manifest_path
        self._on_ptt_press    = on_ptt_press
        self._on_ptt_release  = on_ptt_release
        self._on_stop_tts     = on_stop_tts
        self._on_repeat_tts   = on_repeat_tts
        self._ptt_mode        = ptt_mode      # "ptt_hold" | "ptt_toggle"
        self._ptt_active      = False         # toggle-mode state
        self._stop_event      = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock            = threading.Lock()
        self._import_warned   = False         # log ImportError only once

    # ------------------------------------------------------------------ public

    def start(self) -> None:
        """Start the background polling thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._thread_fn, daemon=True, name="steamvr-input")
        self._thread.start()
        logger.info("SteamVRInputManager started")

    def stop(self) -> None:
        """Signal the thread to exit and wait for it."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        logger.info("SteamVRInputManager stopped")

    def set_ptt_mode(self, mode: str) -> None:
        """Update the PTT mode at runtime (thread-safe)."""
        with self._lock:
            self._ptt_mode = mode
            self._ptt_active = False

    # ----------------------------------------------------------------- private

    def _thread_fn(self) -> None:
        while not self._stop_event.is_set():
            openvr = self._try_init()
            if openvr is None:
                # SteamVR unavailable — wait and retry
                self._stop_event.wait(RETRY_INTERVAL_S)
                continue

            logger.info("SteamVR connected — beginning input polling")
            try:
                self._poll_loop(openvr)
            except Exception as exc:
                logger.warning("SteamVR poll loop exited with error: %s", exc)
            finally:
                try:
                    openvr.shutdown()
                except Exception:
                    pass
                logger.info("SteamVR disconnected — will retry in %ds", RETRY_INTERVAL_S)

    def _try_init(self):
        """Attempt to initialise OpenVR and load action handles.

        Returns the openvr module on success, or None on failure.
        """
        try:
            import openvr
        except (ImportError, OSError) as exc:
            if not self._import_warned:
                logger.warning("openvr unavailable (%s: %s) — will keep retrying", type(exc).__name__, exc)
                self._import_warned = True
            return None

        try:
            openvr.init(openvr.VRApplication_Background)
        except openvr.OpenVRError as exc:
            logger.debug("OpenVR init failed (SteamVR probably not running): %s %r", exc, exc)
            return None

        try:
            vrinput = openvr.VRInput()
            vrinput.setActionManifestPath(self._action_manifest)

            self._action_set_handle = vrinput.getActionSetHandle(ACTION_SET)
            self._h_ptt    = vrinput.getActionHandle(ACT_PTT)
            self._h_stop   = vrinput.getActionHandle(ACT_STOP_TTS)
            self._h_repeat = vrinput.getActionHandle(ACT_REPEAT)

            logger.debug("Action handles loaded OK")
            return openvr
        except Exception as exc:
            logger.warning("Failed to load action handles: %s", exc)
            try:
                openvr.shutdown()
            except Exception:
                pass
            return None

    def _poll_loop(self, openvr) -> None:
        vrinput   = openvr.VRInput()
        vrsystem  = openvr.VRSystem()
        event     = openvr.VREvent_t()

        active_action_set = openvr.VRActiveActionSet_t()
        active_action_set.ulActionSet = self._action_set_handle

        # Per-action previous-state trackers (used to detect transitions ourselves
        # as a fallback; bChanged in the data struct is authoritative when available)
        _prev: dict[int, bool] = {
            self._h_ptt:    False,
            self._h_stop:   False,
            self._h_repeat: False,
        }

        while not self._stop_event.is_set():
            # Check for VREvent_Quit
            while vrsystem.pollNextEvent(event):
                if event.eventType == openvr.VREvent_Quit:
                    logger.info("Received VREvent_Quit")
                    return

            try:
                vrinput.updateActionState([active_action_set])
            except openvr.OpenVRError as exc:
                logger.warning("updateActionState failed: %s", exc)
                return

            # Read each digital action and fire on transitions
            for handle, prev_key, fire_fn in (
                (self._h_ptt,    self._h_ptt,    self._handle_ptt),
                (self._h_stop,   self._h_stop,   self._handle_stop_tts),
                (self._h_repeat, self._h_repeat, self._handle_repeat_tts),
            ):
                try:
                    data = vrinput.getDigitalActionData(handle, openvr.k_ulInvalidInputValueHandle)
                except openvr.OpenVRError:
                    continue

                state = bool(data.bState)
                changed = bool(data.bChanged)

                # Use bChanged from OpenVR when available; fall back to manual edge detection
                if changed:
                    fire_fn(state)
                else:
                    prev = _prev[prev_key]
                    if state != prev:
                        fire_fn(state)
                _prev[prev_key] = state

            time.sleep(POLL_INTERVAL)

    def _handle_ptt(self, state: bool) -> None:
        with self._lock:
            mode = self._ptt_mode

        if mode == "ptt_hold":
            if state:
                self._on_ptt_press()
            else:
                self._on_ptt_release()
        elif mode == "ptt_toggle":
            if state:  # button-down only
                if self._ptt_active:
                    self._on_ptt_release()
                else:
                    self._on_ptt_press()
                self._ptt_active = not self._ptt_active

    def _handle_stop_tts(self, state: bool) -> None:
        if state:  # button-down only
            self._on_stop_tts()

    def _handle_repeat_tts(self, state: bool) -> None:
        if state:  # button-down only
            self._on_repeat_tts()
