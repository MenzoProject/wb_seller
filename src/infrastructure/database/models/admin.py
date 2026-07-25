"""ORM-модель администратора бота."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.log import Log
    from src.infrastructure.database.models.payment import Payment


class Admin(CreatedAtMixin, Base):
    """Администратор бота, имеющий доступ к панели управления.

    Attributes:
        id: Внутренний идентификатор администратора.
        telegram_id: Уникальный идентификатор администратора в Telegram.
        full_name: Полное имя администратора.
        is_super_admin: Признак расширенных прав администратора.
    """

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    processed_payments: Mapped[list["Payment"]] = relationship(
        back_populates="paid_by_admin",
    )
    logs: Mapped[list["Log"]] = relationship(
        back_populates="admin",
    )

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями администратора.
        """
        return (
            f"Admin(id={self.id}, telegram_id={self.telegram_id}, "
            f"full_name={self.full_name!r}, is_super_admin={self.is_super_admin})"
        )
