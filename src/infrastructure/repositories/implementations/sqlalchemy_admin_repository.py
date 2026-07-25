"""Реализация репозитория администраторов на основе SQLAlchemy 2.x Async."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.admin import Admin
from src.infrastructure.database.models.admin import Admin as AdminModel


class SQLAlchemyAdminRepository:
    """Реализация `AdminRepository` поверх асинхронной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий переданной сессией базы данных.

        Args:
            session: Активная асинхронная сессия SQLAlchemy, привязанная
                к текущей единице работы (transaction/unit of work).
        """
        self._session = session

    @staticmethod
    def _to_entity(model: AdminModel) -> Admin:
        """Преобразует ORM-модель администратора в доменную сущность.

        Args:
            model: ORM-модель администратора, полученная из базы данных.

        Returns:
            Доменная сущность администратора.
        """
        return Admin(
            id=model.id,
            telegram_id=model.telegram_id,
            full_name=model.full_name,
            is_super_admin=model.is_super_admin,
            created_at=model.created_at,
        )

    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        """Возвращает администратора по идентификатору Telegram."""
        statement = select(AdminModel).where(AdminModel.telegram_id == telegram_id)
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def create(self, admin: Admin) -> Admin:
        """Создаёт нового администратора в базе данных."""
        model = AdminModel(
            telegram_id=admin.telegram_id,
            full_name=admin.full_name,
            is_super_admin=admin.is_super_admin,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)
