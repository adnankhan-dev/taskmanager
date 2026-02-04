from fastapi import HTTPException, status
from app.models.user import User

def require_login(user: User | None):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

def require_admin(user: User):
    require_login(user)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
from app.utils.hierarchy import can_assign_task


def can_edit_task(user, task):
    if not user or not task:
        return False

    if task.archived or task.status == "Completed":
        return False

    # Admin override
    if user.role == "admin":
        return True

    # Assigned user can edit
    if task.assigned_to_id == user.id:
        return True

    # Manager can edit subordinate tasks (except completed/archived)
    if task.assigned_to and can_assign_task(user, task.assigned_to):
        return True

    return False
