"""Клавиатуры процесса оформления заявки (кнопка отмены, подтверждение получения)."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.texts.user_texts import CANCEL_BUTTON_TEXT, CONFIRM_RECEIVE_BUTTON_TEXT


class CancelApplicationCallback(CallbackData, prefix="app_cancel"):
    """Данные callback-кнопки отмены заявки в процессе оформления.

    Attributes:
        application_id: Внутренний идентификатор отменяемой заявки.
    """

    application_id: int


class ConfirmReceiveCallback(CallbackData, prefix="app_receive"):
    """Данные callback-кнопки подтверждения получения товара.

    Attributes:
        application_id: Внутренний идентификатор заявки, товар по которой получен.
    """

    application_id: int


def get_cancel_application_keyboard(application_id: int) -> InlineKeyboardMarkup:
    """Формирует клавиатуру с единственной кнопкой отмены оформляемой заявки.

    Args:
        application_id: Внутренний идентификатор заявки, находящейся в процессе оформления.

    Returns:
        Инлайн-клавиатура с кнопкой «❌ Отмена».
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=CANCEL_BUTTON_TEXT,
        callback_data=CancelApplicationCallback(application_id=application_id).pack(),
    )
    return builder.as_markup()


def get_confirm_receive_keyboard(application_id: int) -> InlineKeyboardMarkup:
    """Формирует клавиатуру с кнопкой подтверждения получения товара.

    Args:
        application_id: Внутренний идентификатор заявки, ожидающей получения товара.

    Returns:
        Инлайн-клавиатура с кнопкой «✅ Я получил(а) товар».
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=CONFIRM_RECEIVE_BUTTON_TEXT,
        callback_data=ConfirmReceiveCallback(application_id=application_id).pack(),
    )
    return builder.as_markup()
