"""Обработчик входа в панель администратора.

Раздел «⚙ Настройки» обрабатывается отдельным роутером
(`src.bot.handlers.admin.banks_management`), реализующим управление
справочником банков — единственным подразделом настроек на данный момент.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards.admin.main_menu import get_admin_main_menu_keyboard
from src.bot.texts.admin_texts import ADMIN_WELCOME_TEXT

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
