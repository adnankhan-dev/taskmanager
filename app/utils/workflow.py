from app.utils.hierarchy import can_assign_task


def can_submit_for_review(user, task):
    return task.assigned_to_id == user.id and task.status in [
        "To Do", "In Progress", "Returned"
    ]


def can_review_task(user, task):
    if not task.assigned_to:
        return False

    return can_assign_task(user, task.assigned_to) and task.status == "Submitted for Review"


def can_complete_task(user, task):
    return user.role == "admin" or task.status == "Approved"
