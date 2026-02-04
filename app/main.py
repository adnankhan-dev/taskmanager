from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base
from sqlalchemy import inspect, text
from app.dependencies import get_db
from app.ui import templates

# Routers
from app.routes import auth
from app.routes import task_pages
from app.routes import report_pages
from app.routes import user_pages
from app.routes import task_type_pages
from app.routes import quick_tasks

# Models
from app.models.user import User
from app.models.task_type import TaskType
from app.models.privilege import Privilege
from app.models.quick_task import QuickTask

# Security
from app.utils.security import hash_password
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from app.routes import dashboard


# =====================================================
# APP INITIALIZATION
# =====================================================
app = FastAPI(title=settings.app_name)


# =====================================================
# SESSION MIDDLEWARE
# =====================================================
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie
)

# Static files (logo, CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# =====================================================
# DATABASE INIT
# =====================================================
Base.metadata.create_all(bind=engine)

# =====================================================
# LIGHTWEIGHT SCHEMA UPDATES (SQLITE/DEV SAFE)
# =====================================================
inspector = inspect(engine)
if "tasks" in inspector.get_table_names():
    task_cols = {c["name"] for c in inspector.get_columns("tasks")}
    with engine.begin() as conn:
        if "completion_remarks" not in task_cols:
            conn.execute(
                text("ALTER TABLE tasks ADD COLUMN completion_remarks TEXT")
            )
        if "completed_at" not in task_cols:
            conn.execute(
                text("ALTER TABLE tasks ADD COLUMN completed_at DATETIME")
            )
        if "submission_remarks" not in task_cols:
            conn.execute(
                text("ALTER TABLE tasks ADD COLUMN submission_remarks TEXT")
            )
        if "submitted_at" not in task_cols:
            conn.execute(
                text("ALTER TABLE tasks ADD COLUMN submitted_at DATETIME")
            )


# =====================================================
# GLOBAL TEMPLATE DATA (REPORT FILTERS)
# =====================================================
@app.middleware("http")
async def inject_report_filters(request: Request, call_next):
    response = None
    db: Session | None = None

    try:
        db = next(get_db())
        request.state.task_types = (
            db.query(TaskType)
            .filter(TaskType.is_active == True)
            .all()
        )
        request.state.users = (
            db.query(User)
            .filter(User.is_active == True)
            .all()
        )

        response = await call_next(request)
    finally:
        if db:
            db.close()

    return response


# =====================================================
# ROUTERS
# =====================================================
app.include_router(auth.router)
app.include_router(task_pages.router)
app.include_router(report_pages.router)
app.include_router(user_pages.router)
app.include_router(task_type_pages.router)
app.include_router(dashboard.router)
app.include_router(quick_tasks.router)


# =====================================================
# DASHBOARD ROUTE (ENTRY POINT)
# =====================================================
@app.get("/")
def root():
    return RedirectResponse("/dashboard", status_code=303)


# =====================================================
# ADMIN SEED (FIRST RUN ONLY)
# =====================================================
with Session(engine) as db:
    admin = db.query(User).filter(
        User.username == settings.admin_username
    ).first()

    if not admin:
        db.add(
            User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role="admin",
                full_name="System Administrator",
                department="IT",
                is_active=True
            )
        )
        db.commit()

    # Seed default privileges (first run)
    if not db.query(Privilege).first():
        default_privs = [
            ("TASK_VIEW", "Can view tasks"),
            ("TASK_CREATE", "Can create tasks"),
            ("TASK_EDIT", "Can edit tasks"),
            ("TASK_APPROVE", "Can approve/return tasks"),
            ("REPORT_EXPORT", "Can export reports"),
        ]
        for code, desc in default_privs:
            db.add(Privilege(code=code, description=desc))
        db.commit()
