"""Клавиатура главного меню пользовательского бота."""

from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

MENU_CATALOG = "📦 Каталог"
MENU_MY_APPLICATIONS = "📋 Мои заявки"
MENU_REQUISITES = "💳 Реквизиты"
MENU_INSTRUCTION = "📖 Инструкция"
MENU_SUPPORT = "💬 Поддержка"

MENU_BUTTON_TEXTS = frozenset(
    {MENU_CATALOG, MENU_MY_APPLICATIONS, MENU_REQUISITES, MENU_INSTRUCTION, MENU_SUPPORT}
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Формирует reply-клавиатуру главного меню пользовательского бота.

    Returns:
        Клавиатура с пунктами: Каталог, Мои заявки, Реквизиты, Инструкция, Поддержка.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text=MENU_CATALOG)
    builder.button(text=MENU_MY_APPLICATIONS)
    builder.button(text=MENU_REQUISITES)
    builder.button(text=MENU_INSTRUCTION)
    builder.button(text=MENU_SUPPORT)
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)
