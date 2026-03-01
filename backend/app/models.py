"""
SQLAlchemy ORM models + Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


# ═══════════════════════════════════════════════════════════
#  ORM MODELS
# ═══════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), default="New Conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)          # user | assistant | system
    content = Column(Text, nullable=False)
    input_mode = Column(String(10), default="text")    # text | voice
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


# ═══════════════════════════════════════════════════════════
#  PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════

class MessageSchema(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    input_mode: str = "text"
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageSchema] = []

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    input_mode: Literal["text", "voice"] = "text"


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageSchema
    response: MessageSchema


class TranscriptionResponse(BaseModel):
    text: str
    language: str = "en"
    duration: float = 0.0


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"


class SystemCommandRequest(BaseModel):
    command: str = Field(..., description="Natural-language system command")


class SystemCommandResponse(BaseModel):
    success: bool
    action: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    whisper: bool
    ollama: bool
    tts: bool
    gpu_available: bool
