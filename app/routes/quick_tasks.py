from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date

from app.dependencies import get_db, get_current_user
from app.ui import templates
from app.models.quick_task import QuickTask
from app.models.user import User


router = APIRouter(prefix="/ui/quick-tasks")


@router.get("")
def quick_task_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    q = db.query(QuickTask)
    if user.role != "admin":
        q = q.filter(QuickTask.created_by_id == user.id)

    quick_tasks = q.order_by(QuickTask.completed_on.desc()).all()

    return templates.TemplateResponse(
        "quick_tasks/list.html",
        {"request": request, "quick_tasks": quick_tasks, "user": user}
    )


@router.post("/create")
def quick_task_create(
    title: str = Form(...),
    completed_on: date | None = Form(None),
    notes: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    quick = QuickTask(
        title=title,
        notes=notes,
        completed_on=completed_on or date.today(),
        created_by_id=user.id
    )
    db.add(quick)
    db.commit()

    return RedirectResponse("/ui/quick-tasks", status_code=303)
