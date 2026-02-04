from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.milestone import MilestoneCreate, MilestoneStatusUpdate
from app.services.milestone_service import add_milestone, update_milestone_status
from app.models.task import Task
from app.models.milestone import TaskMilestone
from app.models.user import User
from app.utils.permissions import require_login

router = APIRouter(prefix="/milestones", tags=["Milestones"])

@router.post("/task/{task_id}")
def add_milestone_api(
    task_id: int,
    payload: MilestoneCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    require_login(user)

    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return add_milestone(
        db=db,
        task=task,
        title=payload.title,
        deadline=payload.deadline,
        description=payload.description,
        sequence=payload.sequence
    )


@router.patch("/{milestone_id}/status")
def update_milestone_status_api(
    milestone_id: int,
    payload: MilestoneStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    require_login(user)

    milestone = db.get(TaskMilestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    update_milestone_status(db, milestone, payload.status)
    return {"message": "Status updated"}
