from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.security import verify_password

def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
