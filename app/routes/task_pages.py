from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date

from app.dependencies import get_current_user, get_db
from app.ui import templates

from app.models.user import User
from app.models.task import Task
from app.models.milestone import TaskMilestone
from app.models.task_type import TaskType

from app.services.task_service import (
    create_task,
    update_task,
    submit_for_review,
    approve_task,
    return_task,
    complete_task
)
from app.services.milestone_service import add_milestone, update_milestone_status

from app.utils.hierarchy import get_all_subordinate_ids, can_assign_task
from app.utils.workflow import (
    can_submit_for_review,
    can_review_task,
    can_complete_task
)
from app.utils.permissions import can_edit_task
from app.utils.task_visibility import apply_task_visibility

router = APIRouter(prefix="/ui/tasks")

def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


# =========================
# Task List
# =========================

@router.get("")
def task_list(
    request: Request,
    filter: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    type_id: int | None = None,
    assigned_to_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    today = date.today()
    from_dt = _parse_date(from_date)
    to_dt = _parse_date(to_date)
    q = db.query(Task).filter(Task.archived == False)
    q = apply_task_visibility(q, user)

    # ================= FILTER HANDLING =================
    if filter == "today":
        q = q.filter(Task.final_deadline == today)

    elif filter == "upcoming":
        q = q.filter(Task.final_deadline > today)

    elif filter == "overdue":
        q = q.filter(
            Task.final_deadline < today,
            Task.status != "Completed"
        )

    # ================= FORM FILTERS =================
    if status:
        q = q.filter(Task.status == status)

    if priority:
        q = q.filter(Task.priority == priority)

    if type_id:
        q = q.filter(Task.type_id == type_id)

    if assigned_to_id:
        q = q.filter(Task.assigned_to_id == assigned_to_id)

    if from_dt:
        q = q.filter(Task.final_deadline >= from_dt)

    if to_dt:
        q = q.filter(Task.final_deadline <= to_dt)

    tasks = q.order_by(Task.final_deadline.asc()).all()

    return templates.TemplateResponse(
        "tasks/list.html",
        {
            "request": request,
            "tasks": tasks,
            "user": user,
            "active_filter": filter,
            "filters": {
                "status": status,
                "priority": priority,
                "type_id": type_id,
                "assigned_to_id": assigned_to_id,
                "from_date": from_date,
                "to_date": to_date
            }
        }
    )

# =========================
# Create Task (Form)
# =========================
@router.get("/create")
def create_task_form(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user.role == "admin":
        task_types = db.query(TaskType).filter(TaskType.is_active == True).all()
    else:
        task_types = (
            db.query(TaskType)
            .filter(
                TaskType.department == user.department,
                TaskType.is_active == True
            )
            .all()
        )

    if user.role == "admin":
        assignable_users = db.query(User).filter(User.is_active == True).all()
    else:
        subordinate_ids = get_all_subordinate_ids(user)
        assignable_users = (
            db.query(User)
            .filter(User.id.in_(subordinate_ids + [user.id]))
            .filter(User.is_active == True)
            .all()
            if subordinate_ids else
            db.query(User)
            .filter(User.id == user.id, User.is_active == True)
            .all()
        )

    return templates.TemplateResponse(
        "tasks/create.html",
        {
            "request": request,
            "task_types": task_types,
            "assignable_users": assignable_users,
            "user": user
        }
    )


# =========================
# Create Task (Submit)
# =========================
@router.post("/create")
def create_task_submit(
    title: str = Form(...),
    type_id: int = Form(...),
    priority: str = Form(...),
    final_deadline: date = Form(...),
    folder_link: str | None = Form(None),
    assigned_to_id: str | None = Form(None),
    description: str | None = Form(None),

    milestone_title: list[str] = Form([]),
    milestone_deadline: list[str] = Form([]),

    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    assigned_to_id_val = int(assigned_to_id) if assigned_to_id else None

    # ---- Assignment validation ----
    if assigned_to_id_val:
        assignee = db.get(User, assigned_to_id_val)
        if not assignee or not can_assign_task(user, assignee):
            return RedirectResponse("/dashboard", status_code=403)

    # ---- Create task ----
    task = create_task(
        db=db,
        title=title,
        type_id=type_id,
        final_deadline=final_deadline,
        priority=priority,
        assigned_to_id=assigned_to_id_val,
        folder_link=folder_link,
        description=description
    )

    # ---- Create milestones (Step 8.5) ----
    for idx, (m_title, m_deadline_raw) in enumerate(
        zip(milestone_title, milestone_deadline),
        start=1
    ):
        m_deadline = _parse_date(m_deadline_raw)
        if m_title and m_deadline:
            db.add(
                TaskMilestone(
                    task_id=task.id,
                    title=m_title,
                    deadline=m_deadline,
                    sequence=idx
                )
            )

    db.commit()

    return RedirectResponse("/ui/tasks", status_code=303)


# =========================
# Task Detail
# =========================
@router.get("/{task_id}")
def task_detail(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    task = db.get(Task, task_id)
    if not task:
        return RedirectResponse("/ui/tasks", status_code=303)

    milestones = (
        db.query(TaskMilestone)
        .filter(TaskMilestone.task_id == task_id)
        .order_by(TaskMilestone.sequence)
        .all()
    )

    return templates.TemplateResponse(
        "tasks/detail.html",
        {
            "request": request,
            "task": task,
            "milestones": milestones,
            "user": user
        }
    )


# =========================
# Workflow Actions
# =========================
@router.post("/{task_id}/submit")
def submit_task_for_review(
    task_id: int,
    submission_remarks: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    task = db.get(Task, task_id)
    if not task or not can_submit_for_review(user, task):
        return RedirectResponse("/dashboard", status_code=403)

    submit_for_review(db, task, submission_remarks=submission_remarks)
    return RedirectResponse(f"/ui/tasks/{task_id}", status_code=303)


@router.post("/{task_id}/approve")
def approve_task_submit(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task or not can_review_task(user, task):
        return RedirectResponse("/dashboard", status_code=403)

    approve_task(db, task)
    return RedirectResponse(f"/ui/tasks/{task_id}", status_code=303)


@router.post("/{task_id}/return")
def return_task_submit(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task or not can_review_task(user, task):
        return RedirectResponse("/dashboard", status_code=403)

    return_task(db, task)
    return RedirectResponse(f"/ui/tasks/{task_id}", status_code=303)


@router.post("/{task_id}/complete")
def complete_task_submit(
    task_id: int,
    completion_remarks: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    task = db.get(Task, task_id)
    if not task or not can_complete_task(user, task):
        return RedirectResponse("/dashboard", status_code=403)

    complete_task(db, task, completion_remarks=completion_remarks)
    return RedirectResponse(f"/ui/tasks/{task_id}", status_code=303)


# =========================
# Milestones (Post Creation)
# =========================
@router.post("/{task_id}/milestones")
def add_milestone_submit(
    task_id: int,
    title: str = Form(...),
    deadline: date = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    task = db.get(Task, task_id)
    if task:
        add_milestone(db, task, title, deadline)

    return RedirectResponse(f"/ui/tasks/{task_id}", status_code=303)


@router.post("/milestones/{milestone_id}/status")
def update_milestone_status_submit(
    milestone_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    milestone = db.get(TaskMilestone, milestone_id)
    if milestone:
        update_milestone_status(db, milestone, status)

    return RedirectResponse(f"/ui/tasks/{milestone.task_id}", status_code=303)


# =========================
# Edit Task
# =========================
@router.get("/{task_id}/edit")
def edit_task_form(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    task = db.get(Task, task_id)
    if not task or not can_edit_task(user, task):
        return RedirectResponse("/dashboard", status_code=403)

    if user.role == "admin":
        task_types = db.query(TaskType).filter(TaskType.is_active == True).all()
    else:
        task_types = (
            db.query(TaskType)
            .filter(TaskType.department == user.department, TaskType.is_active == True)
            .all()
        )

    if user.role == "admin":
        assignable_users = db.query(User).filter(User.is_active == True).all()
    else:
        subordinate_ids = get_all_subordinate_ids(user)
        assignable_users = (
            db.query(User)
            .filter(User.id.in_(subordinate_ids + [user.id]))
            .filter(User.is_active == True)
            .all()
            if subordinate_ids else
            db.query(User)
            .filter(User.id == user.id, User.is_active == True)
            .all()
        )

    return templates.TemplateResponse(
        "tasks/edit.html",
        {
            "request": request,
            "task": task,
            "task_types": task_types,
            "assignable_users": assignable_users,
            "user": user
        }
    )


@router.post("/{task_id}/edit")
def edit_task_submit(
    task_id: int,
    title: str = Form(...),
    type_id: int = Form(...),
    priority: str = Form(...),
    final_deadline: date = Form(...),
    folder_link: str | None = Form(None),
    assigned_to_id: str | None = Form(None),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    task = db.get(Task, task_id)
    if not task or not can_edit_task(user, task):
        return RedirectResponse("/dashboard", status_code=403)

    assigned_to_id_val = int(assigned_to_id) if assigned_to_id else None

    update_task(
        db=db,
        task=task,
        title=title,
        type_id=type_id,
        priority=priority,
        final_deadline=final_deadline,
        assigned_to_id=assigned_to_id_val,
        folder_link=folder_link,
        description=description
    )

    return RedirectResponse(f"/ui/tasks/{task_id}", status_code=303)
from app.services.milestone_service import (
    update_milestone,
    delete_milestone,
    move_milestone
)


@router.post("/milestones/{milestone_id}/edit")
def edit_milestone_submit(
    milestone_id: int,
    title: str = Form(...),
    deadline: date = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    milestone = db.get(TaskMilestone, milestone_id)
    if not milestone:
        return RedirectResponse("/ui/tasks", status_code=303)

    update_milestone(db, milestone, title, deadline)
    return RedirectResponse(f"/ui/tasks/{milestone.task_id}", status_code=303)


@router.post("/milestones/{milestone_id}/delete")
def delete_milestone_submit(
    milestone_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    milestone = db.get(TaskMilestone, milestone_id)
    if not milestone:
        return RedirectResponse("/ui/tasks", status_code=303)

    task_id = milestone.task_id
    delete_milestone(db, milestone)
    return RedirectResponse(f"/ui/tasks/{task_id}", status_code=303)


@router.post("/milestones/{milestone_id}/move")
def move_milestone_submit(
    milestone_id: int,
    direction: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    milestone = db.get(TaskMilestone, milestone_id)
    if milestone:
        move_milestone(db, milestone, direction)

    return RedirectResponse(f"/ui/tasks/{milestone.task_id}", status_code=303)
