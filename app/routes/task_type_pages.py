from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.ui import templates
from app.models.task_type import TaskType
from app.models.user import User

router = APIRouter(prefix="/ui/task-types")


# =========================
# List Task Types
# =========================
@router.get("")
def list_task_types(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    types = (
        db.query(TaskType)
        .order_by(TaskType.department, TaskType.name)
        .all()
    )

    departments = (
        db.query(User.department)
        .filter(User.department.isnot(None))
        .distinct()
        .order_by(User.department)
        .all()
    )
    department_options = [row[0] for row in departments if row[0]]

    return templates.TemplateResponse(
        "task_types/list.html",
        {
            "request": request,
            "types": types,
            "departments": department_options,
            "user": user
        }
    )


# =========================
# Create Task Type
# =========================
@router.post("/create")
def create_task_type(
    name: str = Form(...),
    department: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    department_val = department.strip()
    if not department_val:
        return RedirectResponse("/ui/task-types", status_code=303)

    db.add(TaskType(
        name=name.strip(),
        department=department_val,
        is_active=True
    ))
    db.commit()

    return RedirectResponse("/ui/task-types", status_code=303)


# =========================
# Toggle Active / Inactive
# =========================
@router.post("/{type_id}/toggle")
def toggle_task_type(
    type_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    task_type = db.get(TaskType, type_id)
    if task_type and task_type.department == user.department:
        task_type.is_active = not task_type.is_active
        db.commit()

    return RedirectResponse("/ui/task-types", status_code=303)
