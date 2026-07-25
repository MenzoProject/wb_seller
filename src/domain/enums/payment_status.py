"""Статусы выплаты по заявке."""

from __future__ import annotations

import enum


class PaymentStatus(str, enum.Enum):
    """Статусы выплаты денежных средств по заявке.

    Attributes:
        PENDING: Выплата ожидает исполнения администратором.
        PAID: Выплата произведена и подтверждена администратором.
    """

    PENDING = "PENDING"
    PAID = "PAID"
