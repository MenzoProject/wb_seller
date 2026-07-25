"""Интерфейс репозитория для работы с выплатами по заявкам."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol

from src.domain.entities.payment import Payment


class PaymentRepository(Protocol):
    """Абстракция доступа к данным выплат, не зависящая от СУБД."""

    async def get_by_id(self, payment_id: int) -> Payment | None:
        """Возвращает выплату по внутреннему идентификатору.

        Args:
            payment_id: Внутренний идентификатор выплаты.

        Returns:
            Найденная выплата либо None, если выплата не существует.
        """

    async def get_by_application_id(self, application_id: int) -> Payment | None:
        """Возвращает выплату, связанную с указанной заявкой.

        Args:
            application_id: Внутренний идентификатор заявки.

        Returns:
            Найденная выплата либо None, если для заявки ещё не создана выплата.
        """

    async def create(self, payment: Payment) -> Payment:
        """Создаёт новую запись о выплате.

        Args:
            payment: Доменная сущность выплаты без присвоенного `id`.

        Returns:
            Созданная выплата с присвоенным внутренним идентификатором.
        """

    async def update(self, payment: Payment) -> Payment:
        """Обновляет данные существующей выплаты.

        Args:
            payment: Доменная сущность выплаты с заполненным `id`.

        Returns:
            Обновлённая сущность выплаты.

        Raises:
            EntityNotFoundError: Если выплата с указанным `id` не найдена.
        """

    async def list_pending(self, limit: int = 50, offset: int = 0) -> list[Payment]:
        """Возвращает страницу выплат, ожидающих исполнения администратором.

        Args:
            limit: Максимальное количество выплат в результате.
            offset: Количество выплат, которые нужно пропустить.

        Returns:
            Список выплат в статусе PENDING, упорядоченный по дате создания
            (старые вначале).
        """

    async def count_pending(self) -> int:
        """Возвращает количество выплат, ожидающих исполнения.

        Returns:
            Количество выплат в статусе PENDING.
        """

    async def sum_paid_amount(self, since: date | None = None) -> Decimal:
        """Возвращает суммарный объём произведённых выплат.

        Args:
            since: Если указано, учитываются только выплаты, произведённые
                начиная с этой даты. Если не указано, учитываются все выплаты.

        Returns:
            Суммарная сумма выплат в статусе PAID.
        """
