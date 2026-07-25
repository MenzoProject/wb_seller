"""Перечисления доменного слоя."""

from src.domain.enums.application_status import ApplicationStatus
from src.domain.enums.payment_status import PaymentStatus
from src.domain.enums.user_role import UserRole

__all__ = [
    "ApplicationStatus",
    "PaymentStatus",
    "UserRole",
]
