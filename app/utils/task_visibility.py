from sqlalchemy import and_, or_
from app.models.task import Task
from app.utils.hierarchy import get_all_subordinate_ids


def apply_task_visibility(query, user):
    """
    Scope task queries to what the current user should see.
    Rules:
    - Admin: all tasks
    - Non-admin:
      - Own tasks, except "Submitted for Review"
      - Subordinate tasks only when they are "Submitted for Review"
    """
    if not user or user.role == "admin":
        return query

    subordinate_ids = get_all_subordinate_ids(user)

    own_clause = and_(
        Task.assigned_to_id == user.id,
        Task.status != "Submitted for Review"
    )

    if subordinate_ids:
        review_clause = and_(
            Task.assigned_to_id.in_(subordinate_ids),
            Task.status == "Submitted for Review"
        )
        return query.filter(or_(own_clause, review_clause))

    return query.filter(own_clause)
