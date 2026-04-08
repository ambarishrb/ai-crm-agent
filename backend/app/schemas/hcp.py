from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class HCPOut(BaseModel):
    id: UUID
    full_name: str
    specialty: Optional[str] = None
    organization: Optional[str] = None

    model_config = {"from_attributes": True}
