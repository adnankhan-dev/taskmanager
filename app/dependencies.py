from fastapi import Request, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)
from app.models.task_type import TaskType
from app.models.user import User

def inject_report_filters(request: Request, db: Session = Depends(get_db)):
    request.state.task_types = db.query(TaskType).filter(TaskType.is_active == True).all()
    request.state.users = db.query(User).filter(User.is_active == True).all()
