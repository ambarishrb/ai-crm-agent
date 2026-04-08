from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate


def create_interaction(db: Session, data: InteractionCreate) -> Interaction:
    interaction = Interaction(
        hcp_id=data.hcp_id,
        interaction_type=data.interaction_type,
        interaction_date=data.interaction_date,
        interaction_time=data.interaction_time,
        attendees=data.attendees,
        topics_discussed=data.topics_discussed,
        sentiment=data.sentiment,
        outcomes=data.outcomes,
        follow_up_actions=data.follow_up_actions,
        ai_suggested_followups=data.ai_suggested_followups,
        ai_summary=data.ai_summary,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_interaction(db: Session, interaction_id: UUID) -> Optional[Interaction]:
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def list_interactions(db: Session, hcp_id: Optional[UUID] = None) -> List[Interaction]:
    query = db.query(Interaction)
    if hcp_id:
        query = query.filter(Interaction.hcp_id == hcp_id)
    return query.order_by(Interaction.created_at.desc()).all()


def update_interaction(db: Session, interaction_id: UUID, data: InteractionUpdate) -> Optional[Interaction]:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction


def delete_interaction(db: Session, interaction_id: UUID) -> bool:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        return False
    db.delete(interaction)
    db.commit()
    return True


def delete_all_interactions(db: Session) -> int:
    count = db.query(Interaction).count()
    db.query(Interaction).delete()
    db.commit()
    return count
