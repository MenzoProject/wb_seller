"""Клавиатуры и callback-фабрики административного управления справочником банков."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.texts.admin_texts import ADD_BANK_BUTTON_TEXT, format_admin_bank_list_item
from src.domain.entities.bank import Bank


class AdminBanksCallback(CallbackData, prefix="a_bank"):
    """Данные callback-кнопок раздела управления справочником банков.

    Attributes:
        action: Действие: 'list' — показать список банков, 'toggle' —
            включить/отключить банк, 'create' — начать добавление нового банка.
        bank_id: Идентификатор банка (для действия 'toggle').
    """

    action: str
    bank_id: int = 0


def get_admin_banks_list_keyboard(banks: list[Bank]) -> InlineKeyboardMarkup:
    """Формирует клавиатуру справочника банков для панели администратора.

    Каждый банк отображается отдельной кнопкой с пометкой текущего
    статуса; нажатие переключает его доступность для выбора пользователями.

    Args:
        banks: Полный список банков (активных и деактивированных).

    Returns:
        Инлайн-клавиатура со списком банков и кнопкой добавления нового банка.
    """
    builder = InlineKeyboardBuilder()
    for bank in banks:
        builder.button(
            text=format_admin_bank_list_item(bank),
            callback_data=AdminBanksCallback(action="toggle", bank_id=bank.id or 0).pack(),
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text=ADD_BANK_BUTTON_TEXT,
            callback_data=AdminBanksCallback(action="create").pack(),
        )
    )
    return builder.as_markup()


def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Формирует клавиатуру раздела «⚙ Настройки» панели администратора.

    Returns:
        Инлайн-клавиатура с точками входа в подразделы настроек.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🏦 Банки",
        callback_data=AdminBanksCallback(action="list").pack(),
    )
    builder.adjust(1)
    return builder.as_markup()
