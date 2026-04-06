from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, List, Optional


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str = "vereda-small-echo"
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = Field(default=1024, ge=16, le=8192)
    stream: bool = False
    session_id: Optional[int] = None


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

