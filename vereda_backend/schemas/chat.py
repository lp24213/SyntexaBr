from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, List, Optional


class ChatMessage(BaseModel):
    """Compatível com OpenAI: campos extra (tool_calls, etc.) preservados no model_dump."""

    model_config = ConfigDict(extra="allow")

    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    model: str = "vereda-small-echo"
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = Field(default=8192, ge=16, le=16384)
    stream: bool = False
    session_id: Optional[int] = None
    locale: Optional[str] = None


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length"]


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    id: str
    object: Literal["chat.completion"]
    model: str
    choices: List[ChatChoice]
    usage: Optional[ChatUsage] = None


class ChatSessionSummary(BaseModel):
    id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChatMessageItem(BaseModel):
    id: int
    role: Literal["system", "user", "assistant"]
    content: str
    created_at: datetime

