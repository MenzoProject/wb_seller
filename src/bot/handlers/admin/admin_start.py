"""Обработчик входа в панель администратора и заглушка для раздела настроек.

Раздел «⚙ Настройки» не был детализирован в исходном техническом задании
и остаётся зарезервированным для будущих административных инструментов
(управление списком администраторов, банков и т.д.).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards.admin.main_menu import ADMIN_MENU_SETTINGS, get_admin_main_menu_keyboard
from src.bot.texts.admin_texts import ADMIN_COMING_SOON_TEXT, ADMIN_WELCOME_TEXT

router = Router(name="admin_start")


@router.message(Command("admin"))
async def handle_admin_start(message: Message) -> None:
    """Открывает панель администратора по команде /admin.

    Доступ к этому обработчику уже ограничен `AdminAccessMiddleware`,
    подключённым к административному роутеру, поэтому дополнительных
    проверок прав внутри хендлера не требуется.

    Args:
        message: Входящее сообщение с командой /admin.
    """
    await message.answer(ADMIN_WELCOME_TEXT, reply_markup=get_admin_main_menu_keyboard())


@router.message(F.text == ADMIN_MENU_SETTINGS)
async def handle_admin_settings_coming_soon(message: Message) -> None:
    """Отвечает временным сообщением на раздел «⚙ Настройки».

    Args:
        message: Входящее сообщение с текстом кнопки «⚙ Настройки».
    """
    await message.answer(ADMIN_COMING_SOON_TEXT)
