import uuid
from datetime import date, time, datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Date, Time, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.hcp import HCP


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    hcp_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("hcps.id"), nullable=True)
    interaction_type: Mapped[Optional[str]] = mapped_column(String(50))
    interaction_date: Mapped[Optional[date]] = mapped_column(Date)
    interaction_time: Mapped[Optional[time]] = mapped_column(Time)
    attendees: Mapped[Optional[str]] = mapped_column(Text)
    topics_discussed: Mapped[Optional[str]] = mapped_column(Text)
    sentiment: Mapped[Optional[str]] = mapped_column(String(20))
    outcomes: Mapped[Optional[str]] = mapped_column(Text)
    follow_up_actions: Mapped[Optional[str]] = mapped_column(Text)
    ai_suggested_followups: Mapped[Optional[dict]] = mapped_column(JSONB)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    hcp: Mapped[Optional["HCP"]] = relationship(back_populates="interactions")

    @property
    def hcp_name(self) -> Optional[str]:
        return self.hcp.full_name if self.hcp else None
