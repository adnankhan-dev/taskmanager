from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.ui import templates
from app.models.user import User
from app.models.privilege import Privilege
from app.utils.security import hash_password

router = APIRouter(prefix="/ui/users")


@router.get("")
def user_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    users = db.query(User).order_by(User.username).all()
    managers = users

    return templates.TemplateResponse(
        "users/list.html",
        {"request": request, "users": users, "managers": managers, "user": user}
    )


@router.get("/create")
def create_user_form(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    privileges = db.query(Privilege).order_by(Privilege.code).all()
    managers = db.query(User).all()

    return templates.TemplateResponse(
        "users/create.html",
        {
            "request": request,
            "privileges": privileges,
            "managers": managers,
            "user": user
        }
    )


@router.post("/create")
def create_user_submit(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    department: str = Form(...),
    manager_id: int | None = Form(None),
    privilege_ids: list[int] = Form([]),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    username_val = username.strip()
    if not username_val:
        return RedirectResponse("/ui/users/create", status_code=303)

    existing = db.query(User).filter(User.username == username_val).first()
    if existing:
        return RedirectResponse("/ui/users/create", status_code=303)

    new_user = User(
        username=username_val,
        password_hash=hash_password(password),
        role=role.strip(),
        department=department.strip() or None,
        manager_id=manager_id
    )

    if privilege_ids:
        new_user.privileges = (
            db.query(Privilege)
            .filter(Privilege.id.in_(privilege_ids))
            .all()
        )

    db.add(new_user)
    db.commit()

    return RedirectResponse("/ui/users", status_code=303)


@router.get("/{user_id}/edit")
def edit_user_form(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    target = db.get(User, user_id)
    if not target:
        return RedirectResponse("/ui/users", status_code=303)

    privileges = db.query(Privilege).order_by(Privilege.code).all()
    managers = (
        db.query(User)
        .filter(User.id != user_id)
        .order_by(User.username)
        .all()
    )
    selected_privilege_ids = {p.id for p in target.privileges}

    return templates.TemplateResponse(
        "users/edit.html",
        {
            "request": request,
            "target_user": target,
            "privileges": privileges,
            "selected_privilege_ids": selected_privilege_ids,
            "managers": managers,
            "user": user
        }
    )


@router.post("/{user_id}/edit")
def edit_user_submit(
    user_id: int,
    username: str = Form(...),
    role: str = Form(...),
    department: str | None = Form(None),
    manager_id: int | None = Form(None),
    password: str | None = Form(None),
    is_active: str | None = Form(None),
    privilege_ids: list[int] = Form([]),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    target = db.get(User, user_id)
    if not target:
        return RedirectResponse("/ui/users", status_code=303)

    username_val = username.strip()
    if not username_val:
        return RedirectResponse(f"/ui/users/{user_id}/edit", status_code=303)

    duplicate = (
        db.query(User)
        .filter(User.username == username_val, User.id != user_id)
        .first()
    )
    if duplicate:
        return RedirectResponse(f"/ui/users/{user_id}/edit", status_code=303)

    target.username = username_val
    target.role = role.strip()
    target.department = (department or "").strip() or None
    target.manager_id = None if manager_id == user_id else manager_id
    target.is_active = bool(is_active)

    password_val = (password or "").strip()
    if password_val:
        target.password_hash = hash_password(password_val)

    if privilege_ids:
        target.privileges = (
            db.query(Privilege)
            .filter(Privilege.id.in_(privilege_ids))
            .all()
        )
    else:
        target.privileges = []

    db.commit()
    return RedirectResponse("/ui/users", status_code=303)


@router.post("/{user_id}/manager")
def update_user_manager(
    user_id: int,
    manager_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    target = db.get(User, user_id)
    if not target:
        return RedirectResponse("/ui/users", status_code=303)

    if manager_id == user_id:
        return RedirectResponse("/ui/users", status_code=303)

    target.manager_id = manager_id or None
    db.commit()

    return RedirectResponse("/ui/users", status_code=303)
