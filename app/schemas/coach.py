from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class CoachChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list)


class CoachChatResponse(BaseModel):
    reply: str
    retrieved_topics: List[str] = Field(default_factory=list)
    context_summary: Optional[Dict[str, object]] = None
