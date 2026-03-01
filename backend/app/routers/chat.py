"""
Chat router — handles text chat, streaming responses, and conversation management.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    ChatRequest,
    ChatResponse,
    Conversation,
    ConversationListItem,
    ConversationSchema,
    Message,
    MessageSchema,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


# ══════════════════════════════════════════════════════════
#  Chat endpoint (non-streaming)
# ══════════════════════════════════════════════════════════
@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and receive a complete response."""
    # Resolve or create conversation
    conversation = await _get_or_create_conversation(db, req.conversation_id)

    # Persist user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=req.message,
        input_mode=req.input_mode,
    )
    db.add(user_msg)
    await db.flush()

    # Build LLM context from history
    history = await _get_history(db, conversation.id)
    messages = llm_service.build_messages(req.message, history=history)

    # Generate response
    try:
        response_text = await llm_service.chat(messages)
    except Exception as exc:
        logger.error("LLM error: %s", exc)
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

    # Update conversation title if first exchange
    if len(history) == 0:
        conversation.title = req.message[:100]
    conversation.updated_at = datetime.now(timezone.utc)

    await db.flush()

    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageSchema.model_validate(user_msg),
        response=MessageSchema.model_validate(assistant_msg),
    )


# ══════════════════════════════════════════════════════════
#  Chat endpoint (streaming via SSE)
# ══════════════════════════════════════════════════════════
@router.post("/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Stream response tokens via Server-Sent Events."""
    conversation = await _get_or_create_conversation(db, req.conversation_id)

    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=req.message,
        input_mode=req.input_mode,
    )
    db.add(user_msg)
    await db.flush()

    history = await _get_history(db, conversation.id, exclude_last=True)
    messages = llm_service.build_messages(req.message, history=history)

    if len(history) == 0:
        conversation.title = req.message[:100]
    conversation.updated_at = datetime.now(timezone.utc)
    await db.flush()

    assistant_msg_id = str(uuid.uuid4())

    async def event_stream():
        full_response: list[str] = []
        # Send conversation metadata
        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation.id, 'message_id': assistant_msg_id})}\n\n"

        try:
            async for token in llm_service.chat_stream(messages):
                full_response.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            complete_text = "".join(full_response)
            yield f"data: {json.dumps({'type': 'done', 'content': complete_text})}\n\n"

            # Persist assistant response after streaming completes
            async with db.begin_nested():
                asst_msg = Message(
                    id=assistant_msg_id,
                    conversation_id=conversation.id,
                    role="assistant",
                    content=complete_text,
                    input_mode="text",
                )
                db.add(asst_msg)
                await db.flush()

        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════
#  Conversations CRUD
# ══════════════════════════════════════════════════════════
@router.get("/conversations", response_model=list[ConversationListItem])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """List all conversations with message count, newest first."""
    stmt = (
        select(
            Conversation,
            func.count(Message.id).label("msg_count"),
        )
        .outerjoin(Message)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        ConversationListItem(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=count,
        )
        for conv, count in rows
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Get a conversation with all its messages."""
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Eager load messages
    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    messages = (await db.execute(stmt)).scalars().all()
    conv_schema = ConversationSchema.model_validate(conv)
    conv_schema.messages = [MessageSchema.model_validate(m) for m in messages]
    return conv_schema


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a conversation and all its messages."""
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    return {"status": "deleted", "id": conversation_id}


@router.delete("/conversations")
async def clear_all_conversations(db: AsyncSession = Depends(get_db)):
    """Delete all conversations."""
    result = await db.execute(select(Conversation))
    convs = result.scalars().all()
    for conv in convs:
        await db.delete(conv)
    return {"status": "cleared", "count": len(convs)}


# ══════════════════════════════════════════════════════════
#  Helpers
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
    """Fetch recent messages formatted for the LLM."""
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
