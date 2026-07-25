"""Middleware автоматической регистрации пользователей и проверки блокировки."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.application.services.user_service import UserService


class UserRegistrationMiddleware(BaseMiddleware):
    """Регистрирует пользователя при первом обращении и блокирует доступ забаненным.

    При каждом входящем сообщении или callback-запросе от реального
    пользователя (не бота) middleware находит либо создаёт соответствующую
    запись в базе данных через `UserService.get_or_create` и помещает её
    в `data["current_user"]`. Если пользователь заблокирован
    администратором, дальнейшая обработка апдейта прекращается.

    Должен быть зарегистрирован после `ServicesMiddleware`, так как
    использует `user_service` из контекстных данных.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Регистрирует пользователя и прерывает обработку при блокировке.

        Args:
            handler: Следующий обработчик в цепочке middlewares.
            event: Обрабатываемый объект апдейта Telegram.
            data: Словарь контекстных данных, передаваемых обработчику.

        Returns:
            Результат выполнения следующего обработчика в цепочке, либо
            `None`, если пользователь заблокирован и обработка прервана.
        """
        telegram_user = data.get("event_from_user")
        if telegram_user is None or telegram_user.is_bot:
            return await handler(event, data)

        user_service: UserService = data["user_service"]
        current_user = await user_service.get_or_create(
            telegram_id=telegram_user.id,
            full_name=telegram_user.full_name,
            username=telegram_user.username,
        )

        if current_user.is_blocked:
            if isinstance(event, Message):
                await event.answer(
                    "🚫 Вы заблокированы и не можете пользоваться ботом. "
                    "Если считаете это ошибкой, обратитесь в поддержку."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Вы заблокированы.", show_alert=True)
            return None

        data["current_user"] = current_user
        return await handler(event, data)
