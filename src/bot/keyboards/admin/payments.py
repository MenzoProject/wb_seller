"""Клавиатуры и callback-фабрика административного управления выплатами."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminPaymentsCallback(CallbackData, prefix="a_pay"):
    """Данные callback-кнопок раздела управления выплатами.

    Attributes:
        action: Действие: 'list' — страница списка выплат, 'mark_paid' —
            отметить выплату произведённой.
        application_id: Идентификатор заявки, к которой относится выплата.
        page: Номер страницы списка, к которой относится действие.
    """

    action: str
    application_id: int = 0
    page: int = 0


def get_admin_payments_list_keyboard(
    items: list[tuple[int, str]], page: int, has_next_page: bool
) -> InlineKeyboardMarkup:
    """Формирует клавиатуру списка выплат, ожидающих исполнения.

    Args:
        items: Список пар (идентификатор заявки, подпись кнопки).
        page: Номер текущей страницы (с нуля).
        has_next_page: Есть ли следующая страница выплат.

    Returns:
        Инлайн-клавиатура: каждая кнопка сразу отмечает соответствующую
        выплату произведённой, плюс навигация по страницам.
    """
    builder = InlineKeyboardBuilder()
    for application_id, label in items:
        builder.button(
            text=label,
            callback_data=AdminPaymentsCallback(
                action="mark_paid", application_id=application_id, page=page
            ).pack(),
        )
    builder.adjust(1)

    navigation_buttons: list[InlineKeyboardButton] = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=AdminPaymentsCallback(action="list", page=page - 1).pack(),
            )
        )
    if has_next_page:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=AdminPaymentsCallback(action="list", page=page + 1).pack(),
            )
        )
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()
