"""ORM-модель журнала (аудит-лога) действий в системе."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.admin import Admin
    from src.infrastructure.database.models.user import User


class Log(CreatedAtMixin, Base):
    """Запись журнала действий пользователя или администратора.

    Используется для аудита ключевых событий системы: создание заявок,
    смена статусов, действия администраторов и т.д.

    Attributes:
        id: Внутренний идентификатор записи журнала.
        user_id: Идентификатор пользователя, совершившего действие
            (может отсутствовать, если действие совершил администратор).
        admin_id: Идентификатор администратора, совершившего действие
            (может отсутствовать, если действие совершил пользователь).
        action: Краткий машиночитаемый код действия (например,
            'application_status_changed', 'product_created').
        entity_type: Тип сущности, к которой относится действие
            (например, 'Application', 'Product').
        entity_id: Идентификатор сущности, к которой относится действие.
        payload: Дополнительные структурированные данные о событии в
            формате JSON (например, старый и новый статус заявки).
    """

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="logs")
    admin: Mapped["Admin | None"] = relationship(back_populates="logs")

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями записи журнала.
        """
        return (
            f"Log(id={self.id}, action={self.action!r}, "
            f"entity_type={self.entity_type!r}, entity_id={self.entity_id})"
        )
