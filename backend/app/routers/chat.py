import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.agent.graph import invoke_agent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = invoke_agent(
            db=db,
            user_message=request.message,
            form_data=request.current_form_state,
            interaction_id=request.interaction_id,
        )
        return ChatResponse(
            reply=result["reply"],
            form_updates=result.get("form_updates"),
            tool_used=result.get("tool_used"),
            interaction_id=result.get("interaction_id"),
        )
    except Exception as e:
        logger.exception("Chat agent error")
        return ChatResponse(
            reply=f"Sorry, I encountered an error processing your request. Please try again. ({type(e).__name__})",
            form_updates=None,
            tool_used=None,
            interaction_id=request.interaction_id,
        )
