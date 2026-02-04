from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.services.auth_service import authenticate_user
from app.dependencies import get_db
from app.ui import templates

router = APIRouter()

@router.get("/login")
def login_page(request: Request, error: int | None = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error}
    )

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)
    if not user:
        return RedirectResponse("/login?error=1", status_code=303)

    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=303)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
