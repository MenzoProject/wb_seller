"""Обработчик раздела «📖 Инструкция»."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from src.bot.keyboards.user.main_menu import MENU_INSTRUCTION
from src.bot.texts.user_texts import INSTRUCTION_TEXT

router = Router(name="user_instructions")


@router.message(F.text == MENU_INSTRUCTION)
async def handle_instruction(message: Message) -> None:
    """Отправляет пользователю общую инструкцию по использованию бота.

    Args:
        message: Входящее сообщение с текстом кнопки «📖 Инструкция».
    """
    await message.answer(INSTRUCTION_TEXT)
