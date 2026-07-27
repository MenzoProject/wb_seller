"""DI-контейнер приложения.

`DIContainer` — единственная точка сборки зависимостей: он хранит
долгоживущие объекты (настройки, подключение к базе данных) и по
запросу собирает набор сервисов (`ServiceContainer`), связанных с
конкретной асинхронной сессией SQLAlchemy. Такой подход обеспечивает,
что все репозитории, использованные при обработке одного апдейта
Telegram, работают в рамках одной транзакции (unit of work).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.admin_service import AdminService
from src.application.services.application_service import ApplicationService
from src.application.services.payment_service import PaymentService
from src.application.services.product_service import ProductService
from src.application.services.requisites_service import RequisitesService
from src.application.services.statistics_service import StatisticsService
from src.application.services.user_service import UserService
from src.config.settings import AppSettings
from src.infrastructure.database.engine import Database
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


@dataclass(slots=True)
class ServiceContainer:
    """Набор полностью собранных сервисов, привязанных к одной сессии БД.

    Attributes:
        user_service: Сервис работы с пользователями.
        admin_service: Сервис работы с администраторами.
        product_service: Сервис работы с товарами каталога.
        application_service: Сервис работы с заявками.
        payment_service: Сервис работы с выплатами.
        requisites_service: Сервис работы с реквизитами пользователей.
        statistics_service: Сервис агрегированной статистики.
    """

    user_service: UserService
    admin_service: AdminService
    product_service: ProductService
    application_service: ApplicationService
    payment_service: PaymentService
    requisites_service: RequisitesService
    statistics_service: StatisticsService


class DIContainer:
    """Контейнер внедрения зависимостей приложения.

    Хранит долгоживущие объекты (настройки и подключение к базе данных) и
    предоставляет фабричный метод `build_services` для сборки сервисов,
    привязанных к конкретной сессии SQLAlchemy — как правило, одной на
    каждый обрабатываемый апдейт Telegram.
    """

    def __init__(self, settings: AppSettings, database: Database) -> None:
        """Инициализирует контейнер настройками приложения и подключением к БД.

        Args:
            settings: Полностью инициализированные настройки приложения.
            database: Инициализированное подключение к базе данных.
        """
        self._settings = settings
        self._database = database

    @property
    def settings(self) -> AppSettings:
        """Возвращает настройки приложения.

        Returns:
            Полностью инициализированный объект настроек приложения.
        """
        return self._settings

    @property
    def database(self) -> Database:
        """Возвращает объект подключения к базе данных.

        Returns:
            Инициализированный экземпляр `Database`.
        """
        return self._database

    def build_services(self, session: AsyncSession) -> ServiceContainer:
        """Собирает полный набор сервисов, работающих в рамках переданной сессии.

        Все репозитории, используемые собранными сервисами, разделяют одну
        и ту же сессию, поэтому все изменения, сделанные при обработке
        одного апдейта Telegram, фиксируются в базе данных атомарно —
        одним commit при успешном завершении обработчика.

        Args:
            session: Активная асинхронная сессия SQLAlchemy для текущей
                единицы работы.

        Returns:
            Полностью собранный `ServiceContainer` со всеми сервисами приложения.
        """
        user_repository = SQLAlchemyUserRepository(session)
        admin_repository = SQLAlchemyAdminRepository(session)
        product_repository = SQLAlchemyProductRepository(session)
        application_repository = SQLAlchemyApplicationRepository(session)
        payment_repository = SQLAlchemyPaymentRepository(session)
        requisites_repository = SQLAlchemyRequisitesRepository(session)
        log_repository = SQLAlchemyLogRepository(session)

        return ServiceContainer(
            user_service=UserService(user_repository),
            admin_service=AdminService(admin_repository),
            product_service=ProductService(product_repository, log_repository),
            application_service=ApplicationService(
                application_repository=application_repository,
                product_repository=product_repository,
                payment_repository=payment_repository,
                requisites_repository=requisites_repository,
                log_repository=log_repository,
                session=session,
            ),
            payment_service=PaymentService(
                payment_repository=payment_repository,
                application_repository=application_repository,
                log_repository=log_repository,
                session=session,
            ),
            requisites_service=RequisitesService(requisites_repository),
            statistics_service=StatisticsService(
                user_repository=user_repository,
                product_repository=product_repository,
                application_repository=application_repository,
                payment_repository=payment_repository,
            ),
        )
