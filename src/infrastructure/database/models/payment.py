"""ORM-модель выплаты по заявке."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums.payment_status import PaymentStatus
from src.infrastructure.database.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.admin import Admin
    from src.infrastructure.database.models.application import Application


class Payment(CreatedAtMixin, Base):
    """Выплата кэшбэка пользователю по заявке.

    Attributes:
        id: Внутренний идентификатор выплаты.
        application_id: Идентификатор заявки, к которой относится выплата
            (одна заявка — одна выплата).
        amount: Сумма выплаты.
        status: Текущий статус выплаты.
        paid_by_admin_id: Идентификатор администратора, отметившего выплату
            произведённой.
        paid_at: Дата и время фактического подтверждения выплаты.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            name="payment_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    paid_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="payment")
    paid_by_admin: Mapped["Admin | None"] = relationship(back_populates="processed_payments")

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями выплаты.
        """
        return (
            f"Payment(id={self.id}, application_id={self.application_id}, "
            f"amount={self.amount}, status={self.status.value})"
        )
