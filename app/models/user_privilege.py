from sqlalchemy import Table, Column, ForeignKey
from app.database import Base

user_privileges = Table(
    "user_privileges",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("privilege_id", ForeignKey("privileges.id"), primary_key=True),
)
