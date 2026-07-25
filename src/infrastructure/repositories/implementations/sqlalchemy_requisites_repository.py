"""Реализация репозитория реквизитов и банков на основе SQLAlchemy 2.x Async."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.bank import Bank
from src.domain.entities.requisites import UserRequisites
from src.domain.exceptions.base import EntityNotFoundError
from src.infrastructure.database.models.bank import Bank as BankModel
from src.infrastructure.database.models.user_requisites import (
    UserRequisites as UserRequisitesModel,
)


class SQLAlchemyRequisitesRepository:
    """Реализация `RequisitesRepository` поверх асинхронной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий переданной сессией базы данных.

        Args:
            session: Активная асинхронная сессия SQLAlchemy, привязанная
                к текущей единице работы (transaction/unit of work).
        """
        self._session = session

    @staticmethod
    def _to_entity(model: UserRequisitesModel) -> UserRequisites:
        """Преобразует ORM-модель реквизитов в доменную сущность.

        Args:
            model: ORM-модель реквизитов, полученная из базы данных.

        Returns:
            Доменная сущность реквизитов пользователя.
        """
        return UserRequisites(
            id=model.id,
            user_id=model.user_id,
            full_name=model.full_name,
            phone=model.phone,
            bank_id=model.bank_id,
            is_default=model.is_default,
            created_at=model.created_at,
        )

    @staticmethod
    def _bank_to_entity(model: BankModel) -> Bank:
        """Преобразует ORM-модель банка в доменную сущность.

        Args:
            model: ORM-модель банка, полученная из базы данных.

        Returns:
            Доменная сущность банка.
        """
        return Bank(id=model.id, name=model.name, is_active=model.is_active)

    async def get_by_id(self, requisites_id: int) -> UserRequisites | None:
        """Возвращает набор реквизитов по внутреннему идентификатору."""
        model = await self._session.get(UserRequisitesModel, requisites_id)
        return self._to_entity(model) if model is not None else None

    async def list_by_user(self, user_id: int) -> list[UserRequisites]:
        """Возвращает все сохранённые наборы реквизитов пользователя."""
        statement = (
            select(UserRequisitesModel)
            .where(UserRequisitesModel.user_id == user_id)
            .order_by(UserRequisitesModel.created_at.desc())
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_default_for_user(self, user_id: int) -> UserRequisites | None:
        """Возвращает набор реквизитов пользователя, используемый по умолчанию."""
        statement = select(UserRequisitesModel).where(
            UserRequisitesModel.user_id == user_id,
            UserRequisitesModel.is_default.is_(True),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def create(self, requisites: UserRequisites) -> UserRequisites:
        """Создаёт новый набор реквизитов пользователя."""
        model = UserRequisitesModel(
            user_id=requisites.user_id,
            full_name=requisites.full_name,
            phone=requisites.phone,
            bank_id=requisites.bank_id,
            is_default=requisites.is_default,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, requisites: UserRequisites) -> UserRequisites:
        """Обновляет данные существующего набора реквизитов."""
        model = await self._session.get(UserRequisitesModel, requisites.id)
        if model is None:
            entity_id = requisites.id if requisites.id is not None else 0
            raise EntityNotFoundError("Реквизиты", entity_id)

        model.full_name = requisites.full_name
        model.phone = requisites.phone
        model.bank_id = requisites.bank_id
        model.is_default = requisites.is_default

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, requisites_id: int) -> None:
        """Удаляет набор реквизитов пользователя."""
        model = await self._session.get(UserRequisitesModel, requisites_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def unset_default_for_user(
        self, user_id: int, exclude_id: int | None = None
    ) -> None:
        """Снимает признак использования по умолчанию со всех реквизитов пользователя."""
        statement = (
            update(UserRequisitesModel)
            .where(
                UserRequisitesModel.user_id == user_id,
                UserRequisitesModel.is_default.is_(True),
            )
            .values(is_default=False)
        )
        if exclude_id is not None:
            statement = statement.where(UserRequisitesModel.id != exclude_id)

        await self._session.execute(statement)
        await self._session.flush()

    async def list_active_banks(self) -> list[Bank]:
        """Возвращает список банков, доступных для выбора пользователем."""
        statement = (
            select(BankModel)
            .where(BankModel.is_active.is_(True))
            .order_by(BankModel.name.asc())
        )
        result = await self._session.execute(statement)
        return [self._bank_to_entity(model) for model in result.scalars().all()]

    async def get_bank_by_id(self, bank_id: int) -> Bank | None:
        """Возвращает банк по внутреннему идентификатору."""
        model = await self._session.get(BankModel, bank_id)
        return self._bank_to_entity(model) if model is not None else None
