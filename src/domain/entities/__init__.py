"""Доменные сущности приложения.

Доменные сущности — это чистые Python-объекты (без зависимости от
SQLAlchemy или aiogram), инкапсулирующие бизнес-правила и инварианты
предметной области. Репозитории преобразуют ORM-модели в доменные
сущности и обратно, что позволяет сервисам работать с бизнес-логикой,
не зная о деталях хранения данных.
"""

from src.domain.entities.admin import Admin
from src.domain.entities.application import Application
from src.domain.entities.bank import Bank
from src.domain.entities.log import Log
from src.domain.entities.payment import Payment
from src.domain.entities.product import Product
from src.domain.entities.requisites import UserRequisites
from src.domain.entities.user import User

__all__ = [
    "Admin",
    "Application",
    "Bank",
    "Log",
    "Payment",
    "Product",
    "User",
    "UserRequisites",
]
