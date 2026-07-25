"""ORM-модель пользователя (реселлера)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.application import Application
    from src.infrastructure.database.models.log import Log
    from src.infrastructure.database.models.user_requisites import UserRequisites


class User(TimestampMixin, Base):
    """Пользователь бота — реселлер Wildberries или Ozon.

    Attributes:
        id: Внутренний идентификатор пользователя.
        telegram_id: Уникальный идентификатор пользователя в Telegram.
        username: Username пользователя в Telegram (без символа @), может отсутствовать.
        full_name: Полное имя пользователя, отображаемое в Telegram.
        phone: Номер телефона пользователя, если был предоставлен.
        is_blocked: Признак блокировки пользователя администратором.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )
    requisites: Mapped[list["UserRequisites"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )
    logs: Mapped[list["Log"]] = relationship(
        back_populates="user",
    )

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями пользователя.
        """
        return (
            f"User(id={self.id}, telegram_id={self.telegram_id}, "
            f"full_name={self.full_name!r}, is_blocked={self.is_blocked})"
        )
