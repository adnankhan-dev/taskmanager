from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.dependencies import get_current_user
from app.ui import templates
from app.models.user import User
from app.services.dashboard_service import get_dashboard_data
from app.dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/login")
def login_page(request: Request, error: int | None = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error}
    )


@router.get("/dashboard")
def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    dashboard = get_dashboard_data(db)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "dashboard": dashboard
        }
    )

@router.get("/")
def root_redirect():
    return RedirectResponse("/dashboard")
