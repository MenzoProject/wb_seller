"""Сервис бизнес-логики работы с пользователями."""

from __future__ import annotations

import logging

from src.domain.entities.user import User
from src.domain.exceptions.base import EntityNotFoundError
from src.infrastructure.repositories.interfaces.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Сервис, инкапсулирующий бизнес-логику работы с пользователями бота."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Инициализирует сервис репозиторием пользователей.

        Args:
            user_repository: Реализация репозитория пользователей.
        """
        self._user_repository = user_repository

    async def get_or_create(
        self, telegram_id: int, full_name: str, username: str | None
    ) -> User:
        """Возвращает существующего пользователя либо регистрирует нового.

        Вызывается при получении команды /start: если пользователь с таким
        telegram_id уже зарегистрирован, возвращает его (актуализируя имя
        и username при необходимости), иначе создаёт новую запись.

        Args:
            telegram_id: Уникальный идентификатор пользователя в Telegram.
            full_name: Текущее полное имя пользователя в Telegram.
            username: Текущий username пользователя в Telegram (без '@').

        Returns:
            Доменная сущность пользователя — существующая или только что созданная.
        """
        existing_user = await self._user_repository.get_by_telegram_id(telegram_id)
        if existing_user is not None:
            if existing_user.full_name != full_name or existing_user.username != username:
                existing_user.full_name = full_name
                existing_user.username = username
                existing_user = await self._user_repository.update(existing_user)
            return existing_user

        new_user = User(
            id=None,
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
        )
        created_user = await self._user_repository.create(new_user)
        logger.info("Зарегистрирован новый пользователь telegram_id=%s", telegram_id)
        return created_user

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Возвращает пользователя по идентификатору Telegram.

        Args:
            telegram_id: Уникальный идентификатор пользователя в Telegram.

        Returns:
            Найденный пользователь либо None, если пользователь не зарегистрирован.
        """
        return await self._user_repository.get_by_telegram_id(telegram_id)

    async def get_by_id(self, user_id: int) -> User:
        """Возвращает пользователя по внутреннему идентификатору.

        Args:
            user_id: Внутренний идентификатор пользователя.

        Returns:
            Найденная доменная сущность пользователя.

        Raises:
            EntityNotFoundError: Если пользователь с указанным `id` не найден.
        """
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("Пользователь", user_id)
        return user

    async def block_user(self, user_id: int) -> User:
        """Блокирует пользователя, лишая его возможности оформлять заявки.

        Args:
            user_id: Внутренний идентификатор блокируемого пользователя.

        Returns:
            Обновлённая доменная сущность пользователя.

        Raises:
            EntityNotFoundError: Если пользователь с указанным `id` не найден.
        """
        user = await self.get_by_id(user_id)
        user.block()
        updated_user = await self._user_repository.update(user)
        logger.info("Пользователь id=%s заблокирован", user_id)
        return updated_user

    async def unblock_user(self, user_id: int) -> User:
        """Снимает блокировку с пользователя.

        Args:
            user_id: Внутренний идентификатор разблокируемого пользователя.

        Returns:
            Обновлённая доменная сущность пользователя.

        Raises:
            EntityNotFoundError: Если пользователь с указанным `id` не найден.
        """
        user = await self.get_by_id(user_id)
        user.unblock()
        updated_user = await self._user_repository.update(user)
        logger.info("Пользователь id=%s разблокирован", user_id)
        return updated_user

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Возвращает страницу списка зарегистрированных пользователей.

        Args:
            limit: Максимальное количество пользователей в результате.
            offset: Количество пользователей, которые нужно пропустить.

        Returns:
            Список пользователей.
        """
        return await self._user_repository.list_all(limit=limit, offset=offset)

    async def count_users(self) -> int:
        """Возвращает общее количество зарегистрированных пользователей.

        Returns:
            Количество зарегистрированных пользователей.
        """
        return await self._user_repository.count_all()
