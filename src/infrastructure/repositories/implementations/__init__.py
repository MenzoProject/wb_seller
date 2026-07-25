"""Реализации репозиториев на основе SQLAlchemy 2.x Async."""

from src.infrastructure.repositories.implementations.sqlalchemy_admin_repository import (
    SQLAlchemyAdminRepository,
)
from src.infrastructure.repositories.implementations.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from src.infrastructure.repositories.implementations.sqlalchemy_log_repository import (
    SQLAlchemyLogRepository,
)
from src.infrastructure.repositories.implementations.sqlalchemy_payment_repository import (
    SQLAlchemyPaymentRepository,
)
from src.infrastructure.repositories.implementations.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from src.infrastructure.repositories.implementations.sqlalchemy_requisites_repository import (
    SQLAlchemyRequisitesRepository,
)
from src.infrastructure.repositories.implementations.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)

__all__ = [
    "SQLAlchemyAdminRepository",
    "SQLAlchemyApplicationRepository",
    "SQLAlchemyLogRepository",
    "SQLAlchemyPaymentRepository",
    "SQLAlchemyProductRepository",
    "SQLAlchemyRequisitesRepository",
    "SQLAlchemyUserRepository",
]
