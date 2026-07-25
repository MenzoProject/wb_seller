"""Клавиатура и callback-фабрика раздела «Мои заявки»."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ResumeApplicationCallback(CallbackData, prefix="app_resume"):
    """Данные callback-кнопки возобновления шага заявки, прерванного пользователем.

    Attributes:
        action: Какой шаг нужно возобновить: 'review' — отправка скриншота
            отзыва, 'receipt' — отправка ссылки на чек.
        application_id: Внутренний идентификатор заявки.
    """

    action: str
    application_id: int


def get_resume_actions_keyboard(
    actions: list[tuple[str, ResumeApplicationCallback]],
) -> InlineKeyboardMarkup | None:
    """Формирует клавиатуру с кнопками возобновления незавершённых шагов заявок.

    Args:
        actions: Список пар (подпись кнопки, данные callback'а) — по одной
            на каждую заявку, требующую действия пользователя.

    Returns:
        Инлайн-клавиатура с кнопками возобновления, либо None, если список пуст.
    """
    if not actions:
        return None

    builder = InlineKeyboardBuilder()
    for label, callback_data in actions:
        builder.button(text=label, callback_data=callback_data.pack())
    builder.adjust(1)
    return builder.as_markup()
