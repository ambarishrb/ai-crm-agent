from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.hcp import HCP


def search_hcps(db: Session, query: str) -> List[HCP]:
    return db.query(HCP).filter(HCP.full_name.ilike(f"%{query}%")).all()


def get_hcp(db: Session, hcp_id: UUID) -> Optional[HCP]:
    return db.query(HCP).filter(HCP.id == hcp_id).first()
