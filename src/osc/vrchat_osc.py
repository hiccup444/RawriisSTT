from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# VRChat OSC addresses
CHATBOX_INPUT = "/chatbox/input"
STT_LISTENING = "/avatar/parameters/stt_listening"


class VRChatOSC:
    """Thin wrapper around python-osc's SimpleUDPClient for VRChat."""

    def __init__(self, address: str = "127.0.0.1", port: int = 9000) -> None:
        self._address = address
        self._port = port
        self._client = None
        self._connect()

    def _connect(self) -> None:
        try:
            from pythonosc.udp_client import SimpleUDPClient
            self._client = SimpleUDPClient(self._address, self._port)
            logger.info("OSC client connected to %s:%d", self._address, self._port)
        except Exception as exc:
            logger.warning("Failed to create OSC client: %s", exc)
            self._client = None

    def update_config(self, address: str, port: int) -> None:
        self._address = address
        self._port = port
        self._connect()

    def send_chatbox(
        self,
        text: str,
        send_immediately: bool = True,
        play_notification: bool = False,
    ) -> None:
        """Send text to the VRChat chatbox.

        Args:
            text: The text to display.
            send_immediately: If True, send right away without waiting for typing indicator.
            play_notification: If True, play the VRChat notification sound.
        """
        if not self._client:
            logger.warning("OSC client not available — skipping chatbox send")
            return
        try:
            self._client.send_message(CHATBOX_INPUT, [text, send_immediately, play_notification])
            logger.debug("Chatbox OSC → %r", text)
        except Exception as exc:
            logger.warning("OSC send_chatbox failed: %s", exc)

    def send_listening(self, state: bool) -> None:
        """Notify the avatar of the current STT listening state."""
        if not self._client:
            return
        try:
            self._client.send_message(STT_LISTENING, state)
        except Exception as exc:
            logger.warning("OSC send_listening failed: %s", exc)

    @property
    def address(self) -> str:
        return self._address

    @property
    def port(self) -> int:
        return self._port
