"""
Speech-to-Text service using faster-whisper (CTranslate2 backend).
Optimized for RTX 3090 with float16 inference.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
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
        logger.info(
            "Loading Whisper model=%s device=%s compute=%s",
            settings.WHISPER_MODEL_SIZE,
            settings.WHISPER_DEVICE,
            settings.WHISPER_COMPUTE_TYPE,
        )
        self._model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
        logger.info("Whisper model loaded successfully.")

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            raise RuntimeError("STT model not loaded. Call load_model() first.")
        return self._model

    # ──────────────────────────────────────────────────────
    #  Transcription
    # ──────────────────────────────────────────────────────
    async def transcribe_bytes(self, audio_bytes: bytes, language: str = "en") -> dict:
        """
        Transcribe raw audio bytes (WAV/WebM/OGG/MP3) to text.

        Returns: { "text": str, "language": str, "segments": list }
        """
        # Decode audio to float32 numpy array
        audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32")

        # Convert stereo → mono if needed
        if audio_array.ndim > 1:
            audio_array = np.mean(audio_array, axis=1)

        # Resample to 16 kHz if necessary (Whisper expects 16 kHz)
        if sample_rate != 16_000:
            try:
                import resampy
                audio_array = resampy.resample(audio_array, sample_rate, 16_000)
            except ImportError:
                logger.warning(
                    "resampy not installed — skipping resample from %d Hz. "
                    "Install resampy for best accuracy.",
                    sample_rate,
                )

        segments_gen, info = self.model.transcribe(
            audio_array,
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

    async def transcribe_file(self, file_path: str | Path, language: str = "en") -> dict:
        """Transcribe an audio file from disk."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        return await self.transcribe_bytes(path.read_bytes(), language=language)


# Module-level singleton
stt_service = STTService()
