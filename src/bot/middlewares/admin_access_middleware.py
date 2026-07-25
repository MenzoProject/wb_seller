"""Middleware, ограничивающее доступ к роутеру только зарегистрированным администраторам."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class AdminAccessMiddleware(BaseMiddleware):
    """Прерывает обработку апдейта, если пользователь не входит в список администраторов.

    Регистрируется как middleware конкретного роутера (административного),
    а не диспетчера целиком, чтобы не влиять на пользовательские хендлеры.
    Список идентификаторов администраторов передаётся при инициализации из
    настроек приложения (`settings.bot.admin_ids`).
    """

    def __init__(self, admin_ids: list[int]) -> None:
        """Инициализирует middleware списком идентификаторов администраторов.

        Args:
            admin_ids: Список Telegram ID пользователей, имеющих доступ к
                административной части бота.
        """
        self._admin_ids = set(admin_ids)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Проверяет принадлежность пользователя к списку администраторов.

        Args:
            handler: Следующий обработчик в цепочке middlewares.
            event: Обрабатываемый объект апдейта Telegram.
            data: Словарь контекстных данных, передаваемых обработчику.

        Returns:
            Результат выполнения следующего обработчика в цепочке, либо
            `None`, если доступ запрещён.
        """
        telegram_user = data.get("event_from_user")
        if telegram_user is None or telegram_user.id not in self._admin_ids:
            if isinstance(event, Message):
                await event.answer("⛔ Доступ разрешён только администраторам.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён.", show_alert=True)
            return None

        return await handler(event, data)
