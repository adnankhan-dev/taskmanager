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

    new_user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        department=department,
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
