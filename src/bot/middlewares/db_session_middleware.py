"""Middleware, открывающее асинхронную сессию базы данных на время обработки апдейта."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.infrastructure.database.engine import Database


class DbSessionMiddleware(BaseMiddleware):
    """Открывает сессию SQLAlchemy на время обработки одного апдейта Telegram.

    Сессия помещается в `data["session"]` и доступна последующим
    middlewares (в частности, `ServicesMiddleware`) и обработчикам.
    По завершении обработки апдейта сессия автоматически фиксирует
    изменения (`commit`) либо откатывает их (`rollback`) при исключении —
    это реализовано в `Database.session()`.
    """

    def __init__(self, database: Database) -> None:
        """Инициализирует middleware подключением к базе данных.

        Args:
            database: Инициализированный экземпляр `Database`.
        """
        self._database = database

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Оборачивает вызов обработчика открытием и закрытием сессии БД.

        Args:
            handler: Следующий обработчик в цепочке middlewares.
            event: Обрабатываемый объект апдейта Telegram.
            data: Словарь контекстных данных, передаваемых обработчику.

        Returns:
            Результат выполнения следующего обработчика в цепочке.
        """
        async with self._database.session() as session:
            data["session"] = session
            return await handler(event, data)
