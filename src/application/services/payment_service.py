"""Сервис бизнес-логики работы с выплатами по заявкам.

Выплата неразрывно связана с заявкой: подтверждение выплаты администратором
одновременно переводит связанную заявку в финальный статус PAID. Чтобы
избежать циклической зависимости между `ApplicationService` и
`PaymentService`, данный сервис работает с `ApplicationRepository`
напрямую, не обращаясь к `ApplicationService`.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from src.application.dto.payment_dto import MarkPaymentPaidDTO
from src.domain.entities.log import Log
from src.domain.entities.payment import Payment
from src.domain.exceptions.application_exceptions import ApplicationNotFoundError
from src.domain.exceptions.base import EntityNotFoundError
from src.infrastructure.repositories.interfaces.application_repository import (
    ApplicationRepository,
)
from src.infrastructure.repositories.interfaces.log_repository import LogRepository
from src.infrastructure.repositories.interfaces.payment_repository import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис, инкапсулирующий бизнес-логику подтверждения выплат по заявкам."""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        application_repository: ApplicationRepository,
        log_repository: LogRepository,
    ) -> None:
        """Инициализирует сервис необходимыми репозиториями.

        Args:
            payment_repository: Реализация репозитория выплат.
            application_repository: Реализация репозитория заявок (для
                перевода связанной заявки в финальный статус PAID).
            log_repository: Реализация репозитория журнала аудита.
        """
        self._payment_repository = payment_repository
        self._application_repository = application_repository
        self._log_repository = log_repository

    async def get_payment_by_application(self, application_id: int) -> Payment:
        """Возвращает выплату, связанную с указанной заявкой.

        Args:
            application_id: Внутренний идентификатор заявки.

        Returns:
            Найденная доменная сущность выплаты.

        Raises:
            EntityNotFoundError: Если для заявки ещё не создана выплата.
        """
        payment = await self._payment_repository.get_by_application_id(application_id)
        if payment is None:
            raise EntityNotFoundError("Выплата по заявке", application_id)
        return payment

    async def mark_application_paid(self, dto: MarkPaymentPaidDTO) -> Payment:
        """Отмечает выплату по заявке произведённой и переводит заявку в статус PAID.

        Args:
            dto: Идентификатор заявки и идентификатор администратора,
                подтвердившего выплату.

        Returns:
            Обновлённая доменная сущность выплаты в статусе PAID.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            EntityNotFoundError: Если для заявки не создана выплата.
            PaymentAlreadyPaidError: Если выплата уже была отмечена как оплаченная.
            InvalidApplicationTransitionError: Если заявка не в статусе WAIT_PAYMENT.
        """
        application = await self._application_repository.get_by_id(dto.application_id)
        if application is None:
            raise ApplicationNotFoundError(dto.application_id)

        payment = await self.get_payment_by_application(dto.application_id)
        payment.mark_paid(dto.admin_id)
        updated_payment = await self._payment_repository.update(payment)

        application.mark_paid()
        await self._application_repository.update(application)

        await self._log_repository.create(
            Log(
                id=None,
                action="payment_marked_paid",
                entity_type="Payment",
                admin_id=dto.admin_id,
                entity_id=updated_payment.id,
                payload={
                    "application_id": dto.application_id,
                    "amount": str(updated_payment.amount),
                },
            )
        )
        logger.info(
            "Выплата id=%s по заявке id=%s подтверждена администратором id=%s",
            updated_payment.id,
            dto.application_id,
            dto.admin_id,
        )
        return updated_payment

    async def list_pending_payments(self, limit: int = 50, offset: int = 0) -> list[Payment]:
        """Возвращает страницу выплат, ожидающих исполнения администратором.

        Args:
            limit: Максимальное количество выплат в результате.
            offset: Количество выплат, которые нужно пропустить.

        Returns:
            Список выплат в статусе PENDING.
        """
        return await self._payment_repository.list_pending(limit=limit, offset=offset)

    async def count_pending_payments(self) -> int:
        """Возвращает количество выплат, ожидающих исполнения.

        Returns:
            Количество выплат в статусе PENDING.
        """
        return await self._payment_repository.count_pending()

    async def sum_paid_amount(self, since: date | None = None) -> Decimal:
        """Возвращает суммарный объём произведённых выплат.

        Args:
            since: Если указано, учитываются только выплаты, произведённые
                начиная с этой даты.

        Returns:
            Суммарная сумма выплат в статусе PAID.
        """
        return await self._payment_repository.sum_paid_amount(since)
