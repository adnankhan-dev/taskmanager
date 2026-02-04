from sqlalchemy.orm import Session
from datetime import date, datetime
from app.models.task import Task


# =========================
# Create Task
# =========================
def create_task(
    db: Session,
    title: str,
    type_id: int,
    final_deadline: date,
    priority: str,
    assigned_to_id: int | None = None,
    folder_link: str | None = None,
    description: str | None = None,
    start_date: date | None = None
) -> Task:
    """
    Create a new task with:
    - Department-specific task type (FK)
    - Mandatory priority
    - Optional assignment
    - Optional folder path / URL
    """

    task = Task(
        title=title,
        description=description,
        type_id=type_id,
        final_deadline=final_deadline,
        priority=priority,
        assigned_to_id=assigned_to_id,
        folder_link=folder_link,
        start_date=start_date,
        status="To Do"
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# =========================
# Update Task
# =========================
def update_task(
    db: Session,
    task: Task,
    title: str,
    type_id: int,
    priority: str,
    final_deadline: date,
    assigned_to_id: int | None = None,
    folder_link: str | None = None,
    description: str | None = None
):
    task.title = title
    task.type_id = type_id
    task.priority = priority
    task.final_deadline = final_deadline
    task.assigned_to_id = assigned_to_id
    task.folder_link = folder_link
    task.description = description

    db.commit()


# =========================
# Archive Task
# =========================
def archive_task(db: Session, task: Task):
    task.archived = True
    db.commit()


# =========================
# Workflow Actions
# =========================
def submit_for_review(db: Session, task: Task, submission_remarks: str | None = None):
    task.status = "Submitted for Review"
    if submission_remarks is not None:
        task.submission_remarks = submission_remarks.strip() or None
    task.submitted_at = datetime.utcnow()
    db.commit()


def approve_task(db: Session, task: Task):
    task.status = "Approved"
    db.commit()


def return_task(db: Session, task: Task):
    task.status = "Returned"
    db.commit()


def complete_task(db: Session, task: Task, completion_remarks: str | None = None):
    task.status = "Completed"
    if completion_remarks is not None:
        task.completion_remarks = completion_remarks.strip() or None
    task.completed_at = datetime.utcnow()
    db.commit()
