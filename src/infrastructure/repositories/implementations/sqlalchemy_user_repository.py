"""Реализация репозитория пользователей на основе SQLAlchemy 2.x Async."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.exceptions.base import EntityNotFoundError
from src.infrastructure.database.models.user import User as UserModel


class SQLAlchemyUserRepository:
    """Реализация `UserRepository` поверх асинхронной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий переданной сессией базы данных.

        Args:
            session: Активная асинхронная сессия SQLAlchemy, привязанная
                к текущей единице работы (transaction/unit of work).
        """
        self._session = session

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        """Преобразует ORM-модель пользователя в доменную сущность.

        Args:
            model: ORM-модель пользователя, полученная из базы данных.

        Returns:
            Доменная сущность пользователя.
        """
        return User(
            id=model.id,
            telegram_id=model.telegram_id,
            full_name=model.full_name,
            username=model.username,
            phone=model.phone,
            is_blocked=model.is_blocked,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по внутреннему идентификатору."""
        model = await self._session.get(UserModel, user_id)
        return self._to_entity(model) if model is not None else None

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Возвращает пользователя по идентификатору Telegram."""
        statement = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def create(self, user: User) -> User:
        """Создаёт нового пользователя в базе данных."""
        model = UserModel(
            telegram_id=user.telegram_id,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            is_blocked=user.is_blocked,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, user: User) -> User:
        """Обновляет данные существующего пользователя."""
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise EntityNotFoundError("Пользователь", user.id if user.id is not None else 0)

        model.username = user.username
        model.full_name = user.full_name
        model.phone = user.phone
        model.is_blocked = user.is_blocked

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Возвращает страницу списка всех зарегистрированных пользователей."""
        statement = (
            select(UserModel).order_by(UserModel.id.desc()).limit(limit).offset(offset)
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def count_all(self) -> int:
        """Возвращает общее количество зарегистрированных пользователей."""
        statement = select(func.count()).select_from(UserModel)
        result = await self._session.execute(statement)
        return result.scalar_one()
