"""Обработчик раздела «💬 Поддержка»."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from src.bot.keyboards.user.main_menu import MENU_SUPPORT
from src.bot.texts.user_texts import SUPPORT_TEXT_TEMPLATE
from src.config.settings import AppSettings

router = Router(name="user_support")


@router.message(F.text == MENU_SUPPORT)
async def handle_support(message: Message, settings: AppSettings) -> None:
    """Отправляет пользователю контакт менеджера поддержки.

    Args:
        message: Входящее сообщение с текстом кнопки «💬 Поддержка».
        settings: Настройки приложения, внедряемые из workflow-данных диспетчера.
    """
    await message.answer(SUPPORT_TEXT_TEMPLATE.format(username=settings.bot.support_username))
