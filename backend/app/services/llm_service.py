"""
LLM service using Ollama's local HTTP API.
Supports streaming and non-streaming chat completions.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Communicates with a locally-running Ollama instance."""

    _instance: Optional[LLMService] = None
    _client: Optional[httpx.AsyncClient] = None

    def __new__(cls) -> LLMService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ──────────────────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────────────────
    async def initialize(self) -> None:
        """Create a persistent async HTTP client."""
        if self._client is not None:
            return
        self._client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=httpx.Timeout(settings.OLLAMA_TIMEOUT, connect=10.0),
        )
        logger.info("LLM client initialized → %s (%s)", settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)

    async def shutdown(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("LLM client not initialized. Call initialize() first.")
        return self._client

    # ──────────────────────────────────────────────────────
    #  Health
    # ──────────────────────────────────────────────────────
    async def health_check(self) -> bool:
        """Return True if Ollama is reachable."""
        try:
            resp = await self.client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Return names of locally-available Ollama models."""
        try:
            resp = await self.client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as exc:
            logger.error("Failed to list models: %s", exc)
            return []

    # ──────────────────────────────────────────────────────
    #  Chat (non-streaming)
    # ──────────────────────────────────────────────────────
    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Send a chat request and return the full response text.

        :param messages: list of {role, content} dicts
        :param model: override default model
        :param temperature: sampling temperature
        """
        payload = {
            "model": model or settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        resp = await self.client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    # ──────────────────────────────────────────────────────
    #  Chat (streaming)
    # ──────────────────────────────────────────────────────
    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Yield response tokens as they are generated.
        """
        payload = {
            "model": model or settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        async with self.client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                import json
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done", False):
                    break

    # ──────────────────────────────────────────────────────
    #  Utility
    # ──────────────────────────────────────────────────────
    def build_messages(
        self,
        user_message: str,
        history: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> list[dict]:
        """
        Build the messages list for Ollama, injecting the system prompt
        and prior conversation history.
        """
        msgs: list[dict] = []
        msgs.append({"role": "system", "content": system_prompt or settings.SYSTEM_PROMPT})
        if history:
            msgs.extend(history)
        msgs.append({"role": "user", "content": user_message})
        return msgs


# Module-level singleton
llm_service = LLMService()
