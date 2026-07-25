"""Реализация репозитория выплат на основе SQLAlchemy 2.x Async."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.payment import Payment
from src.domain.enums.payment_status import PaymentStatus
from src.domain.exceptions.base import EntityNotFoundError
from src.infrastructure.database.models.payment import Payment as PaymentModel


class SQLAlchemyPaymentRepository:
    """Реализация `PaymentRepository` поверх асинхронной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий переданной сессией базы данных.

        Args:
            session: Активная асинхронная сессия SQLAlchemy, привязанная
                к текущей единице работы (transaction/unit of work).
        """
        self._session = session

    @staticmethod
    def _to_entity(model: PaymentModel) -> Payment:
        """Преобразует ORM-модель выплаты в доменную сущность.

        Args:
            model: ORM-модель выплаты, полученная из базы данных.

        Returns:
            Доменная сущность выплаты.
        """
        return Payment(
            id=model.id,
            application_id=model.application_id,
            amount=model.amount,
            status=model.status,
            paid_by_admin_id=model.paid_by_admin_id,
            paid_at=model.paid_at,
            created_at=model.created_at,
        )

    async def get_by_id(self, payment_id: int) -> Payment | None:
        """Возвращает выплату по внутреннему идентификатору."""
        model = await self._session.get(PaymentModel, payment_id)
        return self._to_entity(model) if model is not None else None

    async def get_by_application_id(self, application_id: int) -> Payment | None:
        """Возвращает выплату, связанную с указанной заявкой."""
        statement = select(PaymentModel).where(PaymentModel.application_id == application_id)
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def create(self, payment: Payment) -> Payment:
        """Создаёт новую запись о выплате."""
        model = PaymentModel(
            application_id=payment.application_id,
            amount=payment.amount,
            status=payment.status,
            paid_by_admin_id=payment.paid_by_admin_id,
            paid_at=payment.paid_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, payment: Payment) -> Payment:
        """Обновляет данные существующей выплаты."""
        model = await self._session.get(PaymentModel, payment.id)
        if model is None:
            entity_id = payment.id if payment.id is not None else 0
            raise EntityNotFoundError("Выплата", entity_id)

        model.amount = payment.amount
        model.status = payment.status
        model.paid_by_admin_id = payment.paid_by_admin_id
        model.paid_at = payment.paid_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def list_pending(self, limit: int = 50, offset: int = 0) -> list[Payment]:
        """Возвращает страницу выплат, ожидающих исполнения администратором."""
        statement = (
            select(PaymentModel)
            .where(PaymentModel.status == PaymentStatus.PENDING)
            .order_by(PaymentModel.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def count_pending(self) -> int:
        """Возвращает количество выплат, ожидающих исполнения."""
        statement = (
            select(func.count())
            .select_from(PaymentModel)
            .where(PaymentModel.status == PaymentStatus.PENDING)
        )
        result = await self._session.execute(statement)
        return result.scalar_one()

    async def sum_paid_amount(self, since: date | None = None) -> Decimal:
        """Возвращает суммарный объём произведённых выплат."""
        statement = select(func.coalesce(func.sum(PaymentModel.amount), 0)).where(
            PaymentModel.status == PaymentStatus.PAID
        )
        if since is not None:
            statement = statement.where(PaymentModel.paid_at >= since)

        result = await self._session.execute(statement)
        return Decimal(result.scalar_one())
