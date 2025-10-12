from datetime import datetime
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Text,
    Boolean,
    Enum,
    DateTime,
)


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.now()
    )
    updated_at = mapped_column(
        DateTime, default=datetime.now(), onupdate=datetime.now()
    )
    language_code: Mapped[str] = mapped_column(String, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
