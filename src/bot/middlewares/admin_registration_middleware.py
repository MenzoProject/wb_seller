"""Middleware регистрации администратора в базе данных.

Применяется только к административному роутеру, после того как
`AdminAccessMiddleware` уже подтвердил, что отправитель входит в список
`settings.bot.admin_ids`. Гарантирует, что у каждого администратора
существует соответствующая запись в таблице `admins` с внутренним
идентификатором, используемым как внешний ключ в товарах, заявках,
выплатах и журнале аудита.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.application.services.admin_service import AdminService


class AdminRegistrationMiddleware(BaseMiddleware):
    """Регистрирует администратора при первом обращении к панели управления.

    Должен быть зарегистрирован после `ServicesMiddleware` (использует
    `admin_service` из контекстных данных) и после `AdminAccessMiddleware`
    (полагается на то, что доступ уже проверен).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Регистрирует администратора и добавляет его в контекст обработчика.

        Args:
            handler: Следующий обработчик в цепочке middlewares.
            event: Обрабатываемый объект апдейта Telegram.
            data: Словарь контекстных данных, передаваемых обработчику.

        Returns:
            Результат выполнения следующего обработчика в цепочке.
        """
        telegram_user = data.get("event_from_user")
        if telegram_user is None or telegram_user.is_bot:
            return await handler(event, data)

        admin_service: AdminService = data["admin_service"]
        data["current_admin"] = await admin_service.get_or_create(
            telegram_id=telegram_user.id, full_name=telegram_user.full_name
        )
        return await handler(event, data)
