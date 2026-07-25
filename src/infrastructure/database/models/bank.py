"""ORM-модель банка, используемого в реквизитах пользователей."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.user_requisites import UserRequisites


class Bank(CreatedAtMixin, Base):
    """Банк, доступный для выбора при сохранении реквизитов пользователя.

    Attributes:
        id: Внутренний идентификатор банка.
        name: Название банка, отображаемое пользователю (уникально).
        is_active: Признак того, что банк доступен для выбора в текущий момент.
    """

    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    requisites: Mapped[list["UserRequisites"]] = relationship(back_populates="bank")

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями банка.
        """
        return f"Bank(id={self.id}, name={self.name!r}, is_active={self.is_active})"
