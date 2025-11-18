from datetime import datetime
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.sql import expression
from sqlalchemy import (
    BIGINT,
    Float,
    ForeignKey,
    String,
    Integer,
    Boolean,
    DateTime,
    JSON,
    func,
)
from sqlalchemy.ext.mutable import MutableDict

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=True)
    assistant_id: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    used_promo_codes: Mapped[dict[str, datetime]] = mapped_column(
        MutableDict.as_mutable(JSON), default=dict
    )

    language_code: Mapped[str] = mapped_column(String, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_owner: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=expression.false()
    )
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # description: Mapped[str] = mapped_column(String(255), nullable=True)
    access_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("users.id"), nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=True)
    promo_code_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promo_codes.id"), nullable=True
    )

    activated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")
