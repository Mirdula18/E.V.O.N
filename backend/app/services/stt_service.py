"""
Speech-to-Text service using faster-whisper (CTranslate2 backend).
Optimized for RTX 3090 with float16 inference.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
from faster_whisper import WhisperModel

from app.config import settings

logger = logging.getLogger(__name__)


class STTService:
    """Singleton wrapper around faster-whisper for local speech recognition."""

    _instance: Optional[STTService] = None
    _model: Optional[WhisperModel] = None

    def __new__(cls) -> STTService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ──────────────────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────────────────
    async def load_model(self) -> None:
        """Load the Whisper model into GPU/CPU memory."""
        if self._model is not None:
            return
        device = settings.WHISPER_DEVICE
        compute_type = settings.WHISPER_COMPUTE_TYPE
        logger.info(
            "Loading Whisper model=%s device=%s compute=%s",
            settings.WHISPER_MODEL_SIZE,
            device,
            compute_type,
        )
        try:
            self._model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device=device,
                compute_type=compute_type,
            )
        except Exception as exc:
            if device != "cpu":
                logger.warning(
                    "Failed to load Whisper on %s (%s). Falling back to CPU/float32.",
                    device, exc,
                )
                self._model = WhisperModel(
                    settings.WHISPER_MODEL_SIZE,
                    device="cpu",
                    compute_type="float32",
                )
            else:
                raise
        logger.info("Whisper model loaded successfully.")

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            # Lazy load: try to load the model on first use
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're inside an async context — load synchronously
                    self._load_model_sync()
                else:
                    loop.run_until_complete(self.load_model())
            except RuntimeError:
                self._load_model_sync()
        if self._model is None:
            raise RuntimeError("STT model failed to load. Check logs for details.")
        return self._model

    def _load_model_sync(self) -> None:
        """Synchronous model loading for use when called from a sync property."""
        if self._model is not None:
            return
        device = settings.WHISPER_DEVICE
        compute_type = settings.WHISPER_COMPUTE_TYPE
        logger.info(
            "Lazy-loading Whisper model=%s device=%s compute=%s",
            settings.WHISPER_MODEL_SIZE,
            device,
            compute_type,
        )
        try:
            self._model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device=device,
                compute_type=compute_type,
            )
        except Exception as exc:
            if device != "cpu":
                logger.warning(
                    "Failed to load Whisper on %s (%s). Falling back to CPU/float32.",
                    device, exc,
                )
                self._model = WhisperModel(
                    settings.WHISPER_MODEL_SIZE,
                    device="cpu",
                    compute_type="float32",
                )
            else:
                raise
        logger.info("Whisper model loaded successfully.")

    # ──────────────────────────────────────────────────────
    #  Transcription
    # ──────────────────────────────────────────────────────
    async def transcribe_bytes(self, audio_bytes: bytes, language: str = "en") -> dict:
        """
        Transcribe raw audio bytes (WAV/WebM/OGG/MP3) to text.

        Returns: { "text": str, "language": str, "segments": list }
        """
        # Write to a temp file so faster-whisper can decode any format via PyAV
        # (supports WebM/Opus, WAV, MP3, OGG, FLAC, etc.)
        suffix = ".webm"
        if audio_bytes[:4] == b"RIFF":
            suffix = ".wav"
        elif audio_bytes[:4] == b"fLaC":
            suffix = ".flac"
        elif audio_bytes[:3] == b"ID3" or (len(audio_bytes) > 1 and audio_bytes[:2] == b"\xff\xfb"):
            suffix = ".mp3"
        elif audio_bytes[:4] == b"OggS":
            suffix = ".ogg"

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segments_gen, info = self.model.transcribe(
                tmp_path,
                language=language if language != "auto" else None,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            segments = []
            full_text_parts: list[str] = []
            for seg in segments_gen:
                segments.append(
                    {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
                )
                full_text_parts.append(seg.text.strip())
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        full_text = " ".join(full_text_parts)
        logger.info("Transcribed %d segments, lang=%s", len(segments), info.language)

        return {
            "text": full_text,
            "language": info.language,
            "segments": segments,
        }

    async def transcribe_file(self, file_path: str | Path, language: str = "en") -> dict:
        """Transcribe an audio file from disk."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        segments_gen, info = self.model.transcribe(
            str(path),
            language=language if language != "auto" else None,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        segments = []
        full_text_parts: list[str] = []
        for seg in segments_gen:
            segments.append(
                {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
            )
            full_text_parts.append(seg.text.strip())

        full_text = " ".join(full_text_parts)
        logger.info("Transcribed %d segments, lang=%s", len(segments), info.language)

        return {
            "text": full_text,
            "language": info.language,
            "segments": segments,
        }


# Module-level singleton
stt_service = STTService()
