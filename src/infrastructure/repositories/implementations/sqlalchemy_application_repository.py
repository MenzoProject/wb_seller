"""Реализация репозитория заявок на основе SQLAlchemy 2.x Async."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.application import Application
from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.base import EntityNotFoundError
from src.infrastructure.database.models.application import Application as ApplicationModel

_ACTIVE_STATUS_EXCLUSIONS = (ApplicationStatus.PAID, ApplicationStatus.REJECTED)


class SQLAlchemyApplicationRepository:
    """Реализация `ApplicationRepository` поверх асинхронной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий переданной сессией базы данных.

        Args:
            session: Активная асинхронная сессия SQLAlchemy, привязанная
                к текущей единице работы (transaction/unit of work).
        """
        self._session = session

    @staticmethod
    def _to_entity(model: ApplicationModel) -> Application:
        """Преобразует ORM-модель заявки в доменную сущность.

        Args:
            model: ORM-модель заявки, полученная из базы данных.

        Returns:
            Доменная сущность заявки.
        """
        return Application(
            id=model.id,
            user_id=model.user_id,
            product_id=model.product_id,
            status=model.status,
            article=model.article,
            order_screenshot_file_id=model.order_screenshot_file_id,
            receipt_link=model.receipt_link,
            review_screenshot_file_id=model.review_screenshot_file_id,
            requisites_id=model.requisites_id,
            admin_comment=model.admin_comment,
            payout_due_date=model.payout_due_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, application_id: int) -> Application | None:
        """Возвращает заявку по внутреннему идентификатору."""
        model = await self._session.get(ApplicationModel, application_id)
        return self._to_entity(model) if model is not None else None

    async def create(self, application: Application) -> Application:
        """Создаёт новую заявку в хранилище данных."""
        model = ApplicationModel(
            user_id=application.user_id,
            product_id=application.product_id,
            status=application.status,
            article=application.article,
            order_screenshot_file_id=application.order_screenshot_file_id,
            receipt_link=application.receipt_link,
            review_screenshot_file_id=application.review_screenshot_file_id,
            requisites_id=application.requisites_id,
            admin_comment=application.admin_comment,
            payout_due_date=application.payout_due_date,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, application: Application) -> Application:
        """Обновляет данные существующей заявки."""
        model = await self._session.get(ApplicationModel, application.id)
        if model is None:
            entity_id = application.id if application.id is not None else 0
            raise EntityNotFoundError("Заявка", entity_id)

        model.status = application.status
        model.article = application.article
        model.order_screenshot_file_id = application.order_screenshot_file_id
        model.receipt_link = application.receipt_link
        model.review_screenshot_file_id = application.review_screenshot_file_id
        model.requisites_id = application.requisites_id
        model.admin_comment = application.admin_comment
        model.payout_due_date = application.payout_due_date

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def list_by_user(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Application]:
        """Возвращает страницу заявок конкретного пользователя."""
        statement = (
            select(ApplicationModel)
            .where(ApplicationModel.user_id == user_id)
            .order_by(ApplicationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def list_by_status(
        self, status: ApplicationStatus, limit: int = 50, offset: int = 0
    ) -> list[Application]:
        """Возвращает страницу заявок с указанным статусом."""
        statement = (
            select(ApplicationModel)
            .where(ApplicationModel.status == status)
            .order_by(ApplicationModel.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def list_due_for_payout(self, as_of: date) -> list[Application]:
        """Возвращает заявки, ожидающие выплаты, у которых наступила дата выплаты."""
        statement = (
            select(ApplicationModel)
            .where(
                ApplicationModel.status == ApplicationStatus.WAIT_PAYMENT,
                ApplicationModel.payout_due_date.is_not(None),
                ApplicationModel.payout_due_date <= as_of,
            )
            .order_by(ApplicationModel.payout_due_date.asc())
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def count_by_status(self, status: ApplicationStatus) -> int:
        """Возвращает количество заявок с указанным статусом."""
        statement = (
            select(func.count())
            .select_from(ApplicationModel)
            .where(ApplicationModel.status == status)
        )
        result = await self._session.execute(statement)
        return result.scalar_one()

    async def get_active_application(
        self, user_id: int, product_id: int
    ) -> Application | None:
        """Возвращает активную (не завершённую) заявку пользователя на указанный товар."""
        statement = select(ApplicationModel).where(
            ApplicationModel.user_id == user_id,
            ApplicationModel.product_id == product_id,
            ApplicationModel.status.not_in(_ACTIVE_STATUS_EXCLUSIONS),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None
