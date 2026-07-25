"""ORM-модель сохранённых платёжных реквизитов пользователя."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.application import Application
    from src.infrastructure.database.models.bank import Bank
    from src.infrastructure.database.models.user import User


class UserRequisites(CreatedAtMixin, Base):
    """Платёжные реквизиты пользователя, сохранённые для повторного использования.

    Пользователь может сохранить несколько наборов реквизитов и выбирать
    один из них при оформлении заявки, не вводя данные заново.

    Attributes:
        id: Внутренний идентификатор набора реквизитов.
        user_id: Идентификатор владельца реквизитов.
        full_name: ФИО получателя выплаты.
        phone: Номер телефона, привязанный к банку для перевода.
        bank_id: Идентификатор банка получателя.
        is_default: Признак того, что данный набор реквизитов используется
            по умолчанию при оформлении новой заявки.
    """

    __tablename__ = "user_requisites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    bank_id: Mapped[int] = mapped_column(
        ForeignKey("banks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="requisites")
    bank: Mapped["Bank"] = relationship(back_populates="requisites")
    applications: Mapped[list["Application"]] = relationship(back_populates="requisites")

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями реквизитов.
        """
        return (
            f"UserRequisites(id={self.id}, user_id={self.user_id}, "
            f"full_name={self.full_name!r}, is_default={self.is_default})"
        )
