"""
Voice router — handles audio upload → STT → LLM → TTS pipeline.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Conversation, Message, MessageSchema, TranscriptionResponse
from app.services.llm_service import llm_service
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])


# ══════════════════════════════════════════════════════════
#  Transcribe-only endpoint
# ══════════════════════════════════════════════════════════
@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "en",
):
    """Transcribe uploaded audio to text (Whisper)."""
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        result = await stt_service.transcribe_bytes(audio_bytes, language=language)
    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")

    return TranscriptionResponse(text=result["text"], language=result["language"])


# ══════════════════════════════════════════════════════════
#  Full voice pipeline: Audio → Text → LLM → TTS Audio
# ══════════════════════════════════════════════════════════
@router.post("/pipeline")
async def voice_pipeline(
    audio: UploadFile = File(...),
    conversation_id: str | None = None,
    language: str = "en",
    db: AsyncSession = Depends(get_db),
):
    """
    Complete voice pipeline.
    Accepts audio, returns JSON with transcription + LLM response + TTS audio URL.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # Step 1: STT
    try:
        stt_result = await stt_service.transcribe_bytes(audio_bytes, language=language)
        user_text = stt_result["text"]
    except Exception as exc:
        logger.error("STT failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {exc}")

    if not user_text.strip():
        raise HTTPException(status_code=400, detail="No speech detected in audio")

    # Step 2: Resolve conversation
    conversation = await _get_or_create_conversation(db, conversation_id)

    # Persist user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=user_text,
        input_mode="voice",
    )
    db.add(user_msg)
    await db.flush()

    # Build LLM context
    history = await _get_history(db, conversation.id)
    messages = llm_service.build_messages(user_text, history=history)

    # Step 3: LLM
    try:
        response_text = await llm_service.chat(messages)
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}")

    # Persist assistant message
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        input_mode="text",
    )
    db.add(assistant_msg)

    if not conversation.title or conversation.title == "New Conversation":
        conversation.title = user_text[:100]
    conversation.updated_at = datetime.now(timezone.utc)
    await db.flush()

    # Step 4: TTS
    try:
        audio_wav = await tts_service.synthesize(response_text)
    except Exception as exc:
        logger.warning("TTS failed: %s — returning text only", exc)
        audio_wav = b""

    return {
        "conversation_id": conversation.id,
        "transcription": user_text,
        "response": response_text,
        "user_message": MessageSchema.model_validate(user_msg).model_dump(mode="json"),
        "assistant_message": MessageSchema.model_validate(assistant_msg).model_dump(mode="json"),
        "has_audio": len(audio_wav) > 0,
    }


# ══════════════════════════════════════════════════════════
#  TTS-only endpoint
# ══════════════════════════════════════════════════════════
@router.post("/tts")
async def text_to_speech(text: str):
    """Convert text to speech, returns WAV audio."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    try:
        wav_bytes = await tts_service.synthesize(text)
    except Exception as exc:
        logger.error("TTS failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}")

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=speech.wav"},
    )


# ══════════════════════════════════════════════════════════
#  Voice pipeline with streaming TTS audio
# ══════════════════════════════════════════════════════════
@router.post("/pipeline/stream")
async def voice_pipeline_stream(
    audio: UploadFile = File(...),
    conversation_id: str | None = None,
    language: str = "en",
    db: AsyncSession = Depends(get_db),
):
    """
    Voice pipeline that streams back SSE events:
    - transcription result
    - LLM response tokens
    - final TTS audio (base64)
    """
    import base64

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio")

    # STT
    stt_result = await stt_service.transcribe_bytes(audio_bytes, language=language)
    user_text = stt_result["text"]
    if not user_text.strip():
        raise HTTPException(status_code=400, detail="No speech detected")

    conversation = await _get_or_create_conversation(db, conversation_id)

    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=user_text,
        input_mode="voice",
    )
    db.add(user_msg)
    await db.flush()

    history = await _get_history(db, conversation.id, exclude_last=True)
    msgs = llm_service.build_messages(user_text, history=history)

    if not conversation.title or conversation.title == "New Conversation":
        conversation.title = user_text[:100]
    conversation.updated_at = datetime.now(timezone.utc)
    await db.flush()

    async def event_gen():
        # Emit transcription
        yield f"data: {json.dumps({'type': 'transcription', 'content': user_text, 'conversation_id': conversation.id})}\n\n"

        full_resp: list[str] = []
        try:
            async for token in llm_service.chat_stream(msgs):
                full_resp.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"
            return

        complete = "".join(full_resp)

        # Persist
        asst_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=complete,
            input_mode="text",
        )
        db.add(asst_msg)
        await db.flush()

        # TTS
        try:
            wav = await tts_service.synthesize(complete)
            audio_b64 = base64.b64encode(wav).decode("ascii")
            yield f"data: {json.dumps({'type': 'audio', 'content': audio_b64, 'format': 'wav'})}\n\n"
        except Exception as exc:
            logger.warning("TTS failed in stream: %s", exc)

        yield f"data: {json.dumps({'type': 'done', 'content': complete})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════
#  Helpers (same as chat router)
# ══════════════════════════════════════════════════════════
async def _get_or_create_conversation(
    db: AsyncSession, conversation_id: str | None
) -> Conversation:
    if conversation_id:
        conv = await db.get(Conversation, conversation_id)
        if conv:
            return conv
    conv = Conversation(id=str(uuid.uuid4()))
    db.add(conv)
    await db.flush()
    return conv


async def _get_history(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 20,
    exclude_last: bool = False,
) -> list[dict]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit + (1 if exclude_last else 0))
    )
    rows = (await db.execute(stmt)).scalars().all()
    rows = list(reversed(rows))
    if exclude_last and rows:
        rows = rows[:-1]
    return [{"role": m.role, "content": m.content} for m in rows if m.role != "system"]
