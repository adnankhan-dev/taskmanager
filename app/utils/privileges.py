def has_privilege(user, code: str) -> bool:
    if not user:
        return False

    if user.role == "admin":
        return True

    return any(p.code == code for p in user.privileges)
