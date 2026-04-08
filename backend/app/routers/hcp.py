from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud.hcp import search_hcps, get_hcp
from app.schemas.hcp import HCPOut

router = APIRouter(tags=["HCPs"])


@router.get("/hcps", response_model=list[HCPOut])
def list_hcps(search: str = "", db: Session = Depends(get_db)):
    return search_hcps(db, search)


@router.get("/hcps/{hcp_id}", response_model=HCPOut)
def get_hcp_detail(hcp_id: UUID, db: Session = Depends(get_db)):
    hcp = get_hcp(db, hcp_id)
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp
