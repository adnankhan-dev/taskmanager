from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from math import ceil
from types import SimpleNamespace

from app.dependencies import get_db, get_current_user
from app.ui import templates
from app.models.task import Task
from app.models.quick_task import QuickTask
from app.models.user import User
from app.services.report_service import generate_tasks_excel, generate_tasks_pdf

router = APIRouter(prefix="/ui/reports")

DEFAULT_COLUMNS = [
    "id",
    "title",
    "status",
    "priority",
    "assigned_to",
    "deadline",
    "folder",
    "milestone",
    "milestone_status",
    "milestone_deadline",
]

def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format") from exc


@router.get("")
def report_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),

    # filters
    status: str | None = None,
    priority: str | None = None,
    type_id: int | None = None,
    assigned_to_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    columns: list[str] | None = Query(None),

    # pagination
    page: int = 1
):
    if not user:
        return templates.TemplateResponse("login.html", {"request": request})

    PER_PAGE = 10
    offset = (page - 1) * PER_PAGE

    query = db.query(Task).filter(Task.archived == False)

    # ================= APPLY FILTERS =================
    if status:
        query = query.filter(Task.status == status)

    if priority:
        query = query.filter(Task.priority == priority)

    if type_id:
        query = query.filter(Task.type_id == type_id)

    if assigned_to_id:
        query = query.filter(Task.assigned_to_id == assigned_to_id)

    if from_date:
        query = query.filter(Task.final_deadline >= from_date)

    if to_date:
        query = query.filter(Task.final_deadline <= to_date)

    tasks = query.order_by(Task.final_deadline.asc()).all()

    # Quick logs are treated as completed tasks in reports
    quick_q = db.query(QuickTask)
    if (status and status != "Completed") or priority or type_id:
        quick_tasks = []
    else:
        if from_date:
            quick_q = quick_q.filter(QuickTask.completed_on >= from_date)
        if to_date:
            quick_q = quick_q.filter(QuickTask.completed_on <= to_date)
        if assigned_to_id:
            quick_q = quick_q.filter(QuickTask.created_by_id == assigned_to_id)
        quick_tasks = quick_q.all()

    report_items = []

    for t in tasks:
        t.is_quick = False
        t.url = f"/ui/tasks/{t.id}"
        report_items.append(t)

    for qt in quick_tasks:
        report_items.append(
            SimpleNamespace(
                id=f"Q-{qt.id}",
                title=qt.title,
                status="Completed",
                priority="Normal",
                type=SimpleNamespace(name="Quick Log"),
                assigned_to=qt.created_by,
                final_deadline=qt.completed_on,
                milestones=[],
                folder_link=None,
                is_quick=True,
                url="/ui/quick-tasks"
            )
        )

    report_items.sort(key=lambda x: x.final_deadline or date.min)

    if not columns:
        columns = DEFAULT_COLUMNS

    total = len(report_items)
    total_pages = ceil(total / PER_PAGE) if total else 1
    tasks = report_items[offset:offset + PER_PAGE]

    return templates.TemplateResponse(
        "reports/list.html",
        {
            "request": request,
            "user": user,
            "tasks": tasks,

            # filters (to persist UI state)
            "filters": {
                "status": status,
                "priority": priority,
                "type_id": type_id,
                "assigned_to_id": assigned_to_id,
                "from_date": from_date,
                "to_date": to_date,
                "columns": columns,
            },

            # pagination
            "page": page,
            "total_pages": total_pages,
            "total": total
        }
    )


@router.get("/tasks/excel")
def export_tasks_excel(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    status: str | None = Query(None),
    columns: list[str] | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    output = generate_tasks_excel(
        db,
        _parse_date(from_date),
        _parse_date(to_date),
        status,
        columns
    )

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=tasks_report.xlsx"
        }
    )


@router.get("/tasks/pdf")
def export_tasks_pdf(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    status: str | None = Query(None),
    columns: list[str] | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    output = generate_tasks_pdf(
        db,
        _parse_date(from_date),
        _parse_date(to_date),
        status,
        columns
    )

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=tasks_report.pdf"
        }
    )
