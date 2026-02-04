from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.task import TaskCreate, TaskOut
from app.services.task_service import create_task
from app.utils.permissions import require_login
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskOut)
def create_task_api(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    require_login(user)

    task = create_task(
        db=db,
        title=payload.title,
        task_type=payload.task_type,
        final_deadline=payload.final_deadline,
        description=payload.description,
        priority=payload.priority,
        start_date=payload.start_date
    )
    return task
