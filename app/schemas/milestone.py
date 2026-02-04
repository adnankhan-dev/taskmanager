from pydantic import BaseModel
from datetime import date

class MilestoneCreate(BaseModel):
    title: str
    deadline: date
    description: str | None = None
    sequence: int | None = None

class MilestoneStatusUpdate(BaseModel):
    status: str
