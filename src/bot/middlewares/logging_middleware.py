"""Middleware логирования входящих апдейтов и необработанных исключений."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger("aiogram.updates")


class LoggingMiddleware(BaseMiddleware):
    """Логирует входящие апдейты и перехватывает необработанные исключения хендлеров.

    Регистрируется одним из первых middlewares, чтобы фиксировать в логах
    каждый входящий апдейт независимо от результата его обработки, и
    последним замечать необработанные исключения перед их дальнейшим
    пробросом (что приводит к откату транзакции в `DbSessionMiddleware`).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Логирует апдейт, вызывает следующий обработчик и логирует исключения.

        Args:
            handler: Следующий обработчик в цепочке middlewares.
            event: Обрабатываемый объект апдейта Telegram.
            data: Словарь контекстных данных, передаваемых обработчику.

        Returns:
            Результат выполнения следующего обработчика в цепочке.

        Raises:
            Exception: Исключение, возникшее в обработчике, пробрасывается
                дальше после логирования (для отката транзакции и/или
                отображения ошибки пользователю).
        """
        telegram_user = data.get("event_from_user")
        user_id = telegram_user.id if telegram_user is not None else "unknown"

        if isinstance(event, Message):
            logger.info(
                "Сообщение от %s: %s", user_id, event.text or f"[{event.content_type}]"
            )
        elif isinstance(event, CallbackQuery):
            logger.info("Callback от %s: %s", user_id, event.data)

        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Необработанная ошибка при обработке апдейта от %s", user_id)
            raise
