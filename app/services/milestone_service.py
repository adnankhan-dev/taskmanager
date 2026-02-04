from sqlalchemy.orm import Session
from datetime import datetime
from app.models.milestone import TaskMilestone
from app.models.task import Task

def add_milestone(
    db: Session,
    task: Task,
    title: str,
    deadline,
    description: str | None = None,
    sequence: int | None = None
) -> TaskMilestone:

    if sequence is None:
        sequence = len(task.milestones) + 1

    milestone = TaskMilestone(
        task_id=task.id,
        title=title,
        description=description,
        deadline=deadline,
        sequence=sequence,
        status="Pending"
    )
    
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


def update_milestone_status(
    db: Session,
    milestone: TaskMilestone,
    new_status: str
):
    milestone.status = new_status
    db.commit()

    _auto_complete_task_if_needed(db, milestone.task)


def _auto_complete_task_if_needed(db: Session, task: Task):
    if not task.milestones:
        return  # manual task

    if all(m.status == "Completed" for m in task.milestones):
        task.status = "Completed"
        task.completed_at = task.completed_at or datetime.utcnow()
        db.commit()
def update_milestone(db, milestone, title, deadline):
    milestone.title = title
    milestone.deadline = deadline
    db.commit()


def delete_milestone(db, milestone):
    db.delete(milestone)
    db.commit()


def move_milestone(db, milestone, direction: str):
    """
    direction: 'up' or 'down'
    """
    if direction not in ("up", "down"):
        return

    delta = -1 if direction == "up" else 1
    new_seq = milestone.sequence + delta

    swap = (
        db.query(type(milestone))
        .filter(
            type(milestone).task_id == milestone.task_id,
            type(milestone).sequence == new_seq
        )
        .first()
    )

    if not swap:
        return

    milestone.sequence, swap.sequence = swap.sequence, milestone.sequence
    db.commit()
