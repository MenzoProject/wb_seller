"""Доменная сущность выплаты по заявке."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.domain.enums.payment_status import PaymentStatus
from src.domain.exceptions.application_exceptions import PaymentAlreadyPaidError


@dataclass(slots=True)
class Payment:
    """Выплата кэшбэка пользователю по заявке.

    Attributes:
        id: Внутренний идентификатор выплаты. `None` для ещё не сохранённой
            в базе данных сущности.
        application_id: Идентификатор заявки, к которой относится выплата.
        amount: Сумма выплаты.
        status: Текущий статус выплаты.
        paid_by_admin_id: Идентификатор администратора, отметившего выплату
            произведённой.
        paid_at: Дата и время фактического подтверждения выплаты.
        created_at: Дата и время создания записи о выплате.
    """

    id: int | None
    application_id: int
    amount: Decimal
    status: PaymentStatus = PaymentStatus.PENDING
    paid_by_admin_id: int | None = None
    paid_at: datetime | None = None
    created_at: datetime | None = None

    def mark_paid(self, admin_id: int, paid_at: datetime | None = None) -> None:
        """Отмечает выплату как произведённую конкретным администратором.

        Args:
            admin_id: Идентификатор администратора, подтвердившего выплату.
            paid_at: Дата и время подтверждения выплаты. По умолчанию
                используется текущее время.

        Raises:
            PaymentAlreadyPaidError: Если выплата уже находится в статусе PAID.
        """
        if self.status == PaymentStatus.PAID:
            raise PaymentAlreadyPaidError(self.id)
        self.status = PaymentStatus.PAID
        self.paid_by_admin_id = admin_id
        self.paid_at = paid_at or datetime.now()

    @property
    def is_paid(self) -> bool:
        """Признак того, что выплата уже произведена.

        Returns:
            True, если статус выплаты равен PAID.
        """
        return self.status == PaymentStatus.PAID
