"""Реализация репозитория журнала аудита на основе SQLAlchemy 2.x Async."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.log import Log
from src.infrastructure.database.models.log import Log as LogModel


class SQLAlchemyLogRepository:
    """Реализация `LogRepository` поверх асинхронной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий переданной сессией базы данных.

        Args:
            session: Активная асинхронная сессия SQLAlchemy, привязанная
                к текущей единице работы (transaction/unit of work).
        """
        self._session = session

    @staticmethod
    def _to_entity(model: LogModel) -> Log:
        """Преобразует ORM-модель записи журнала в доменную сущность.

        Args:
            model: ORM-модель записи журнала, полученная из базы данных.

        Returns:
            Доменная сущность записи журнала.
        """
        return Log(
            id=model.id,
            action=model.action,
            entity_type=model.entity_type,
            user_id=model.user_id,
            admin_id=model.admin_id,
            entity_id=model.entity_id,
            payload=model.payload,
            created_at=model.created_at,
        )

    async def create(self, log: Log) -> Log:
        """Создаёт новую запись журнала."""
        model = LogModel(
            user_id=log.user_id,
            admin_id=log.admin_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            payload=log.payload,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def list_by_entity(
        self, entity_type: str, entity_id: int, limit: int = 50
    ) -> list[Log]:
        """Возвращает историю действий, связанных с конкретной сущностью."""
        statement = (
            select(LogModel)
            .where(LogModel.entity_type == entity_type, LogModel.entity_id == entity_id)
            .order_by(LogModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def list_recent(self, limit: int = 50) -> list[Log]:
        """Возвращает последние записи журнала по всем сущностям."""
        statement = select(LogModel).order_by(LogModel.created_at.desc()).limit(limit)
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]
