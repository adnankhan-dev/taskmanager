def get_all_subordinate_ids(user):
    """
    Safely collect all subordinate user IDs under a user.
    Works even if relationships are not yet loaded.
    """

    if not user:
        return []

    ids = []

    def collect(u):
        subs = getattr(u, "subordinates", None)

        if not subs:
            return

        if not isinstance(subs, (list, tuple, set)):
            subs = [subs]

        for sub in subs:
            ids.append(sub.id)
            collect(sub)

    collect(user)
    return ids


def can_assign_task(assigner, assignee):
    """
    Admin can assign to anyone.
    Others can assign only within their hierarchy.
    """
    if not assigner or not assignee:
        return False

    if assigner.role == "admin":
        return True

    if assigner.id == assignee.id:
        return True

    return assignee.id in get_all_subordinate_ids(assigner)
