from typing import Optional, List
from uuid import UUID
from datetime import date, time
from pydantic import BaseModel


class InteractionCreate(BaseModel):
    hcp_id: Optional[UUID] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = "Neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: Optional[List[str]] = None
    ai_summary: Optional[str] = None


class InteractionUpdate(BaseModel):
    hcp_id: Optional[UUID] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: Optional[List[str]] = None
    ai_summary: Optional[str] = None


class InteractionOut(BaseModel):
    id: UUID
    hcp_id: Optional[UUID] = None
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: Optional[list] = None
    ai_summary: Optional[str] = None

    model_config = {"from_attributes": True}
