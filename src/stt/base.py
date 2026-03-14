from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class STTResult:
    text: str
    is_final: bool = True
    confidence: float = 1.0


ResultCallback = Callable[[STTResult], None]


class STTEngine(ABC):
    """Abstract base class for all speech-to-text engines."""

    def __init__(self) -> None:
        self._listening = False
        self._callback: Optional[ResultCallback] = None

    @abstractmethod
    def start_listening(
        self,
        callback: ResultCallback,
        device_index: Optional[int] = None,
        language: str = "en",
    ) -> None:
        """Begin capturing audio and delivering results via *callback*."""

    @abstractmethod
    def stop_listening(self) -> None:
        """Stop capture and free audio resources."""

    def is_listening(self) -> bool:
        return self._listening

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""

    @property
    def requires_model_download(self) -> bool:
        return False
