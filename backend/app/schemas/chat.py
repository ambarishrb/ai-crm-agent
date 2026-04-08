from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    current_form_state: Optional[dict] = None
    interaction_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    form_updates: Optional[dict] = None
    tool_used: Optional[str] = None
    interaction_id: Optional[str] = None
