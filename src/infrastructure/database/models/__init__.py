"""Пакет ORM-моделей базы данных.

Импорт всех моделей в этом файле обязателен: он гарантирует, что каждая
модель зарегистрирована в `Base.metadata` до того, как Alembic будет
собирать метадату для автогенерации миграций, либо до того, как приложение
создаст движок и фабрику сессий.
"""

from src.infrastructure.database.base import Base
from src.infrastructure.database.models.admin import Admin
from src.infrastructure.database.models.application import Application
from src.infrastructure.database.models.bank import Bank
from src.infrastructure.database.models.log import Log
from src.infrastructure.database.models.payment import Payment
from src.infrastructure.database.models.product import Product
from src.infrastructure.database.models.product_photo import ProductPhoto
from src.infrastructure.database.models.user import User
from src.infrastructure.database.models.user_requisites import UserRequisites

__all__ = [
    "Base",
    "Admin",
    "Application",
    "Bank",
    "Log",
    "Payment",
    "Product",
    "ProductPhoto",
    "User",
    "UserRequisites",
]
