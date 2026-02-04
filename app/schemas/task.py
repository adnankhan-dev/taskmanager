from pydantic import BaseModel
from datetime import date

class TaskCreate(BaseModel):
    title: str
    task_type: str
    final_deadline: date
    description: str | None = None
    priority: str | None = None
    start_date: date | None = None

class TaskOut(BaseModel):
    id: int
    title: str
    status: str
    final_deadline: date

    class Config:
        from_attributes = True
