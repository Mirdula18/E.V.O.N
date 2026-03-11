"""
Application-wide configuration via pydantic-settings.
Reads from .env / environment variables with sensible defaults.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Server ────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:3000",
    ]

    # ── Whisper STT ───────────────────────────────────────
    WHISPER_MODEL_SIZE: str = "base"          # tiny | base | small | medium | large-v3
    WHISPER_DEVICE: str = "cuda"              # cuda | cpu
    WHISPER_COMPUTE_TYPE: str = "float16"     # float16 | int8 | float32

    # ── Ollama LLM ────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"              # llama3 | mistral | etc.
    OLLAMA_TIMEOUT: int = 120

    # ── Piper TTS ─────────────────────────────────────────
    PIPER_MODEL_PATH: str = str(BASE_DIR / "models" / "piper" / "en_US-lessac-medium.onnx")
    PIPER_CONFIG_PATH: str = str(BASE_DIR / "models" / "piper" / "en_US-lessac-medium.onnx.json")
    TTS_FALLBACK: str = "pyttsx3"            # pyttsx3 = system TTS fallback
    TTS_SAMPLE_RATE: int = 22050

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'evon.db'}"

    # ── Paths ─────────────────────────────────────────────
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    TTS_OUTPUT_DIR: str = str(BASE_DIR / "data" / "tts_output")

    # ── System Prompt ─────────────────────────────────────
    SYSTEM_PROMPT: str = (
        "You are E.V.O.N. (Enhanced Voice-Operated Nexus), an advanced AI "
        "assistant that runs entirely offline. You are helpful, witty, precise, and "
        "knowledgeable. You respond concisely. When explaining code, you are thorough "
        "but clear. You can help manage system tasks, answer questions, and engage in "
        "natural conversation. Address the user respectfully."
    )


settings = Settings()

# Ensure required directories exist
for dir_path in (settings.UPLOAD_DIR, settings.TTS_OUTPUT_DIR, str(BASE_DIR / "data")):
    Path(dir_path).mkdir(parents=True, exist_ok=True)

Path(BASE_DIR / "models" / "piper").mkdir(parents=True, exist_ok=True)
