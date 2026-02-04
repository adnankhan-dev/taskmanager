from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.database import Base

class Privilege(Base):
    __tablename__ = "privileges"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str]

    users = relationship(
    "User",
    secondary="user_privileges",
    back_populates="privileges"
    )
