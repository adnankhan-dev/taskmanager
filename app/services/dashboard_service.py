from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.milestone import TaskMilestone
from app.utils.task_visibility import apply_task_visibility


def build_dashboard(db: Session, user):
    today = date.today()
    upcoming_limit = today + timedelta(days=7)

    # Base task query
    task_q = db.query(Task).filter(Task.archived == False)
    task_q = apply_task_visibility(task_q, user)

    # ---------- TASK GROUPS ----------
    today_tasks = task_q.filter(
        Task.final_deadline == today,
        Task.status != "Completed"
    ).all()
    upcoming_tasks = task_q.filter(
        Task.final_deadline > today,
        Task.final_deadline <= upcoming_limit,
        Task.status != "Completed"
    ).all()
    overdue_tasks = task_q.filter(
        Task.final_deadline < today,
        Task.status != "Completed"
    ).all()
    pending_review_tasks = task_q.filter(
        Task.status == "Submitted for Review"
    ).all()
    completed_tasks = task_q.filter(
        Task.status == "Completed"
    ).all()

    # ---------- MILESTONE GROUPS ----------
    ms_q = (
        db.query(TaskMilestone)
        .join(TaskMilestone.task)
        .filter(Task.archived == False)
    )
    ms_q = apply_task_visibility(ms_q, user)

    today_milestones = ms_q.filter(TaskMilestone.deadline == today).all()
    upcoming_milestones = ms_q.filter(
        TaskMilestone.deadline > today,
        TaskMilestone.deadline <= upcoming_limit
    ).all()
    overdue_milestones = ms_q.filter(
        TaskMilestone.deadline < today,
        TaskMilestone.status != "Completed"
    ).all()

    return {
        "today": {
            "tasks": today_tasks,
            "milestones": today_milestones,
        },
        "upcoming": {
            "tasks": upcoming_tasks,
            "milestones": upcoming_milestones,
        },
        "overdue": {
            "tasks": overdue_tasks,
            "milestones": overdue_milestones,
        },
        "pending_review": pending_review_tasks,
        "completed": completed_tasks,
    }
