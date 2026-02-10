from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text

from app.database import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
