from sqlalchemy import String, Date, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from app.database import Base

class TaskMilestone(Base):
    __tablename__ = "task_milestones"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    title: Mapped[str]
    description: Mapped[str | None]
    deadline: Mapped[date]
    status: Mapped[str] = mapped_column(default="Pending")  
    sequence: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    task = relationship("Task", back_populates="milestones")
