from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud.interaction import (
    create_interaction,
    get_interaction,
    list_interactions,
    update_interaction,
    delete_interaction,
    delete_all_interactions,
)
from app.schemas.interaction import InteractionCreate, InteractionUpdate, InteractionOut

router = APIRouter(tags=["Interactions"])


@router.post("/interactions", response_model=InteractionOut, status_code=201)
def create(data: InteractionCreate, db: Session = Depends(get_db)):
    return create_interaction(db, data)


@router.get("/interactions", response_model=list[InteractionOut])
def list_all(hcp_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    return list_interactions(db, hcp_id)


@router.get("/interactions/{interaction_id}", response_model=InteractionOut)
def get_one(interaction_id: UUID, db: Session = Depends(get_db)):
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.put("/interactions/{interaction_id}", response_model=InteractionOut)
def update(interaction_id: UUID, data: InteractionUpdate, db: Session = Depends(get_db)):
    interaction = update_interaction(db, interaction_id, data)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.delete("/interactions", status_code=200)
def delete_all(db: Session = Depends(get_db)):
    count = delete_all_interactions(db)
    return {"deleted": count}


@router.delete("/interactions/{interaction_id}", status_code=204)
def delete(interaction_id: UUID, db: Session = Depends(get_db)):
    if not delete_interaction(db, interaction_id):
        raise HTTPException(status_code=404, detail="Interaction not found")
