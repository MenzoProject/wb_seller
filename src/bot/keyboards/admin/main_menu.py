"""Клавиатура главного меню административного бота."""

from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

ADMIN_MENU_PRODUCTS = "📦 Товары"
ADMIN_MENU_REQUESTS = "📋 Заявки"
ADMIN_MENU_PAYMENTS = "💰 Выплаты"
ADMIN_MENU_STATISTICS = "📊 Статистика"
ADMIN_MENU_SETTINGS = "⚙ Настройки"

ADMIN_MENU_BUTTON_TEXTS = frozenset(
    {
        ADMIN_MENU_PRODUCTS,
        ADMIN_MENU_REQUESTS,
        ADMIN_MENU_PAYMENTS,
        ADMIN_MENU_STATISTICS,
        ADMIN_MENU_SETTINGS,
    }
)


def get_admin_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Формирует reply-клавиатуру главного меню администратора.

    Returns:
        Клавиатура с пунктами: Товары, Заявки, Выплаты, Статистика, Настройки.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text=ADMIN_MENU_PRODUCTS)
    builder.button(text=ADMIN_MENU_REQUESTS)
    builder.button(text=ADMIN_MENU_PAYMENTS)
    builder.button(text=ADMIN_MENU_STATISTICS)
    builder.button(text=ADMIN_MENU_SETTINGS)
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)
