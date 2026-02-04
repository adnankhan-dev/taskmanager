from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, DateTime, ForeignKey
from datetime import datetime, date

from app.database import Base


class QuickTask(Base):
    __tablename__ = "quick_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    notes: Mapped[str | None]
    completed_on: Mapped[date] = mapped_column(default=date.today)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by = relationship("User")

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
