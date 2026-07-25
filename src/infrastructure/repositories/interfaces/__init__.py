"""Интерфейсы (протоколы) репозиториев доменного слоя."""

from src.infrastructure.repositories.interfaces.admin_repository import AdminRepository
from src.infrastructure.repositories.interfaces.application_repository import (
    ApplicationRepository,
)
from src.infrastructure.repositories.interfaces.log_repository import LogRepository
from src.infrastructure.repositories.interfaces.payment_repository import PaymentRepository
from src.infrastructure.repositories.interfaces.product_repository import ProductRepository
from src.infrastructure.repositories.interfaces.requisites_repository import (
    RequisitesRepository,
)
from src.infrastructure.repositories.interfaces.user_repository import UserRepository

__all__ = [
    "AdminRepository",
    "ApplicationRepository",
    "LogRepository",
    "PaymentRepository",
    "ProductRepository",
    "RequisitesRepository",
    "UserRepository",
]
