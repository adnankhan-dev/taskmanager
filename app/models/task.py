from sqlalchemy import String, Date, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    # -----------------
    # Core Fields
    # -----------------
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None]

    status: Mapped[str] = mapped_column(default="To Do")
    priority: Mapped[str] = mapped_column(default="Normal")

    # -----------------
    # Task Type
    # -----------------
    type_id: Mapped[int] = mapped_column(ForeignKey("task_types.id"))
    type = relationship("TaskType", back_populates="tasks")

    # -----------------
    # Assignment
    # -----------------
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    assigned_to = relationship("User")

    # -----------------
    # Dates
    # -----------------
    start_date: Mapped[date | None]
    final_deadline: Mapped[date]

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # -----------------
    # Folder / Documents
    # -----------------
    folder_link: Mapped[str | None] = mapped_column(nullable=True)

    # -----------------
    # Completion
    # -----------------
    completion_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    submission_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # -----------------
    # Milestones
    # -----------------
    milestones = relationship(
        "TaskMilestone",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskMilestone.sequence"
    )
