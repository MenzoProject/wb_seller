"""Интерфейс репозитория для работы с администраторами бота."""

from __future__ import annotations

from typing import Protocol

from src.domain.entities.admin import Admin


class AdminRepository(Protocol):
    """Абстракция доступа к данным администраторов, не зависящая от СУБД."""

    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        """Возвращает администратора по идентификатору Telegram.

        Args:
            telegram_id: Уникальный идентификатор администратора в Telegram.

        Returns:
            Найденный администратор либо None, если он ещё не зарегистрирован.
        """

    async def create(self, admin: Admin) -> Admin:
        """Создаёт нового администратора в хранилище данных.

        Args:
            admin: Доменная сущность администратора без присвоенного `id`.

        Returns:
            Созданный администратор с присвоенным внутренним идентификатором.
        """
