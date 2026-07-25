"""Фильтр проверки принадлежности пользователя к списку администраторов."""

from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from src.config.settings import AppSettings


class IsAdminFilter(BaseFilter):
    """Фильтр, пропускающий событие только от зарегистрированного администратора.

    В отличие от `AdminAccessMiddleware`, который ограничивает доступ ко
    всему административному роутеру, этот фильтр удобен для точечной
    проверки прав внутри отдельных обработчиков смешанного роутера
    (например, команда, доступная и пользователям, и администраторам, но
    с разным поведением).
    """

    async def __call__(self, event: Message | CallbackQuery, settings: AppSettings) -> bool:
        """Проверяет, входит ли отправитель события в список администраторов.

        Args:
            event: Обрабатываемое сообщение или callback-запрос.
            settings: Настройки приложения, внедряемые aiogram из
                workflow-данных диспетчера (устанавливаются при старте бота).

        Returns:
            True, если идентификатор отправителя присутствует в
            `settings.bot.admin_ids`, иначе False.
        """
        telegram_user = event.from_user
        return telegram_user is not None and telegram_user.id in settings.bot.admin_ids
