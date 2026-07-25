"""Сервис агрегированной статистики для панели администратора."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from src.domain.enums.application_status import ApplicationStatus
from src.infrastructure.repositories.interfaces.application_repository import (
    ApplicationRepository,
)
from src.infrastructure.repositories.interfaces.payment_repository import PaymentRepository
from src.infrastructure.repositories.interfaces.product_repository import ProductRepository
from src.infrastructure.repositories.interfaces.user_repository import UserRepository


@dataclass(slots=True, frozen=True)
class DashboardStatistics:
    """Агрегированный срез ключевых показателей системы для администратора.

    Attributes:
        total_users: Общее количество зарегистрированных пользователей.
        available_products_count: Количество товаров, доступных в каталоге.
        applications_by_status: Количество заявок в каждом из статусов.
        pending_payments_count: Количество выплат, ожидающих исполнения.
        total_paid_amount: Суммарный объём всех произведённых выплат.
        paid_amount_last_30_days: Суммарный объём выплат за последние 30 дней.
    """

    total_users: int
    available_products_count: int
    applications_by_status: dict[ApplicationStatus, int]
    pending_payments_count: int
    total_paid_amount: Decimal
    paid_amount_last_30_days: Decimal


class StatisticsService:
    """Сервис, инкапсулирующий сбор агрегированной статистики по системе."""

    def __init__(
        self,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        application_repository: ApplicationRepository,
        payment_repository: PaymentRepository,
    ) -> None:
        """Инициализирует сервис репозиториями, необходимыми для сбора статистики.

        Args:
            user_repository: Реализация репозитория пользователей.
            product_repository: Реализация репозитория товаров.
            application_repository: Реализация репозитория заявок.
            payment_repository: Реализация репозитория выплат.
        """
        self._user_repository = user_repository
        self._product_repository = product_repository
        self._application_repository = application_repository
        self._payment_repository = payment_repository

    async def get_dashboard_statistics(self) -> DashboardStatistics:
        """Собирает актуальный агрегированный срез статистики системы.

        Returns:
            Заполненный объект `DashboardStatistics` со всеми ключевыми
            показателями на текущий момент.
        """
        total_users = await self._user_repository.count_all()
        available_products_count = await self._product_repository.count_available()

        applications_by_status: dict[ApplicationStatus, int] = {}
        for status in ApplicationStatus:
            applications_by_status[status] = (
                await self._application_repository.count_by_status(status)
            )

        pending_payments_count = await self._payment_repository.count_pending()
        total_paid_amount = await self._payment_repository.sum_paid_amount()
        paid_amount_last_30_days = await self._payment_repository.sum_paid_amount(
            since=date.today() - timedelta(days=30)
        )

        return DashboardStatistics(
            total_users=total_users,
            available_products_count=available_products_count,
            applications_by_status=applications_by_status,
            pending_payments_count=pending_payments_count,
            total_paid_amount=total_paid_amount,
            paid_amount_last_30_days=paid_amount_last_30_days,
        )
