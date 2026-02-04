from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.ui import templates
from app.services.dashboard_service import build_dashboard
from app.models.task import Task
from app.models.user import User

router = APIRouter()


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    dashboard_data = build_dashboard(db, user)

    # ---- KPI COUNTS ----
    total_tasks = (
        len(dashboard_data["today"]["tasks"])
        + len(dashboard_data["upcoming"]["tasks"])
        + len(dashboard_data["overdue"]["tasks"])
    )

    my_tasks = (
        db.query(Task)
        .filter(
            Task.archived == False,
            Task.assigned_to_id == user.id,
            Task.status != "Submitted for Review"
        )
        .count()
    )
    pending_review = len(dashboard_data.get("pending_review", []))
    overdue = len(dashboard_data["overdue"]["tasks"])
    completed = len(dashboard_data.get("completed", []))

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,

            # unified dashboard object
            "dashboard": dashboard_data,

            # KPIs
            "total_tasks": total_tasks,
            "my_tasks": my_tasks,
            "pending_review": pending_review,
            "overdue": overdue,
            "completed": completed,

            # chart
            "chart_data": {
                "completed": completed,
                "pending_review": pending_review,
                "overdue": overdue,
                "in_progress": max(
                    total_tasks - completed - pending_review - overdue, 0
                )
            }
        }
    )
