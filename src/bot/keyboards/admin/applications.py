"""Клавиатуры и callback-фабрика административного управления заявками."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminApplicationsCallback(CallbackData, prefix="a_app"):
    """Данные callback-кнопок раздела управления заявками.

    Attributes:
        action: Действие: 'queue' — страница очереди заявок на проверку,
            'open' — открыть карточку заявки, 'approve' — одобрить заказ,
            'reject' — отклонить заявку, 'resend' — запросить повторную
            отправку скриншота заказа.
        application_id: Идентификатор заявки (для всех действий, кроме 'queue').
        page: Номер страницы очереди, к которой относится действие.
    """

    action: str
    application_id: int = 0
    page: int = 0


def get_admin_applications_queue_keyboard(
    items: list[tuple[int, str]], page: int, has_next_page: bool
) -> InlineKeyboardMarkup:
    """Формирует клавиатуру очереди заявок, ожидающих проверки.

    Args:
        items: Список пар (идентификатор заявки, подпись кнопки).
        page: Номер текущей страницы (с нуля).
        has_next_page: Есть ли следующая страница заявок.

    Returns:
        Инлайн-клавиатура со списком заявок и навигацией по страницам.
    """
    builder = InlineKeyboardBuilder()
    for application_id, label in items:
        builder.button(
            text=label,
            callback_data=AdminApplicationsCallback(
                action="open", application_id=application_id, page=page
            ).pack(),
        )
    builder.adjust(1)

    navigation_buttons: list[InlineKeyboardButton] = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=AdminApplicationsCallback(action="queue", page=page - 1).pack(),
            )
        )
    if has_next_page:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=AdminApplicationsCallback(action="queue", page=page + 1).pack(),
            )
        )
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


def get_admin_application_card_keyboard(application_id: int, page: int) -> InlineKeyboardMarkup:
    """Формирует клавиатуру карточки заявки с решениями администратора.

    Args:
        application_id: Внутренний идентификатор заявки.
        page: Номер страницы очереди, с которой была открыта карточка.

    Returns:
        Инлайн-клавиатура с кнопками одобрения, отклонения, запроса
        повторной отправки и возврата к очереди.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Одобрить",
        callback_data=AdminApplicationsCallback(
            action="approve", application_id=application_id, page=page
        ).pack(),
    )
    builder.button(
        text="🔄 Запросить повтор",
        callback_data=AdminApplicationsCallback(
            action="resend", application_id=application_id, page=page
        ).pack(),
    )
    builder.button(
        text="❌ Отклонить",
        callback_data=AdminApplicationsCallback(
            action="reject", application_id=application_id, page=page
        ).pack(),
    )
    builder.button(
        text="⬅️ К очереди",
        callback_data=AdminApplicationsCallback(action="queue", page=page).pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


__all__ = [
    "AdminApplicationsCallback",
    "get_admin_application_card_keyboard",
    "get_admin_applications_queue_keyboard",
]
