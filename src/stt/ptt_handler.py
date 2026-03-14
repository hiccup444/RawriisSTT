"""Global PTT (Push-To-Talk) keyboard hook manager."""

from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class PTTHandler:
    """Registers global keyboard hooks for one PTT mode at a time.

    Uses on_press_key / on_release_key so that key-repeat events from holding
    a key are filtered out — press fires exactly once per physical key-down
    and release fires exactly once per physical key-up.

    mode="ptt_hold"   — on_press and on_release both registered
    mode="ptt_toggle" — on_press only; key-up is still tracked internally to
                        reset the _key_down guard so the next toggle works
    """

    def __init__(
        self,
        key: str,
        mode: str,
        on_press: Callable[[], None],
        on_release: Optional[Callable[[], None]] = None,
    ) -> None:
        self._key = key
        self._mode = mode
        self._on_press = on_press
        self._on_release = on_release
        self._hooks: list = []

    def start(self) -> None:
        """Register global keyboard hooks."""
        try:
            import keyboard

            _key_down = False

            def _handle_press(event):
                nonlocal _key_down
                if not _key_down:
                    _key_down = True
                    self._on_press()

            def _handle_release(event):
                nonlocal _key_down
                _key_down = False
                if self._on_release is not None:
                    self._on_release()

            h1 = keyboard.on_press_key(self._key, _handle_press, suppress=False)
            h2 = keyboard.on_release_key(self._key, _handle_release, suppress=False)
            self._hooks = [h1, h2]

            logger.info("PTT hook registered: key=%s  mode=%s", self._key, self._mode)
        except Exception as exc:
            import sys
            if sys.platform != "win32":
                logger.warning(
                    "PTT hook registration failed: %s\n"
                    "On Linux the 'keyboard' library requires read access to /dev/input.\n"
                    "Fix: add your user to the 'input' group —  sudo usermod -aG input $USER  "
                    "— then log out and back in, or run the app as root.",
                    exc,
                )
            else:
                logger.warning("PTT hook registration failed: %s", exc)

    def stop(self) -> None:
        """Unregister all keyboard hooks."""
        try:
            import keyboard
            for h in self._hooks:
                try:
                    keyboard.unhook(h)
                except Exception:
                    pass
        except ImportError:
            pass
        self._hooks = []
        logger.debug("PTT hooks unregistered.")
