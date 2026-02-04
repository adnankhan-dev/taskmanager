from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from datetime import datetime

from app.database import Base
from app.models.user_privilege import user_privileges


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str]
    role: Mapped[str]
    full_name: Mapped[str | None]
    department: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # =========================
    # Dynamic Hierarchy
    # =========================
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    privileges = relationship(
        "Privilege",
        secondary=user_privileges,
        back_populates="users"
    )

    # manager is a single User; subordinates is a collection via backref
    manager = relationship(
        "User",
        remote_side="User.id",
        backref=backref("subordinates", lazy="selectin")
    )
