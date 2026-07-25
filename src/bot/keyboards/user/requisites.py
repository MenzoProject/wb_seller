"""Клавиатуры и callback-фабрики для управления платёжными реквизитами."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.texts.user_texts import REQUISITES_ADD_BUTTON_TEXT, format_requisites_label
from src.domain.entities.bank import Bank
from src.domain.entities.requisites import UserRequisites


class RequisitesCallback(CallbackData, prefix="req"):
    """Данные callback-кнопок раздела самостоятельного управления реквизитами.

    Attributes:
        action: Действие: 'set_default' — сделать основными, 'delete' —
            удалить, 'add' — начать добавление нового набора реквизитов.
        requisites_id: Идентификатор реквизитов (для 'set_default' и 'delete').
    """

    action: str
    requisites_id: int = 0


class ApplicationRequisitesCallback(CallbackData, prefix="app_req"):
    """Данные callback-кнопок выбора реквизитов для конкретной заявки.

    Attributes:
        action: Действие: 'select' — использовать существующий набор
            реквизитов, 'add_new' — указать новые реквизиты.
        application_id: Идентификатор заявки, для которой выбираются реквизиты.
        requisites_id: Идентификатор набора реквизитов (для действия 'select').
    """

    action: str
    application_id: int
    requisites_id: int = 0


class BankSelectCallback(CallbackData, prefix="bank_sel"):
    """Данные callback-кнопки выбора банка при добавлении реквизитов.

    Attributes:
        bank_id: Внутренний идентификатор выбранного банка.
    """

    bank_id: int


def get_requisites_management_keyboard(
    requisites_list: list[UserRequisites], banks_by_id: dict[int, str]
) -> InlineKeyboardMarkup:
    """Формирует клавиатуру раздела самостоятельного управления реквизитами.

    Каждый набор реквизитов отображается строкой из двух кнопок: нажатие
    на подпись назначает набор основным, кнопка «🗑» удаляет его. Ниже
    расположена кнопка добавления нового набора реквизитов.

    Args:
        requisites_list: Список сохранённых реквизитов пользователя.
        banks_by_id: Отображение идентификатора банка в его название.

    Returns:
        Инлайн-клавиатура управления реквизитами.
    """
    builder = InlineKeyboardBuilder()
    for requisites in requisites_list:
        bank_name = banks_by_id.get(requisites.bank_id, "Банк")
        builder.row(
            InlineKeyboardButton(
                text=format_requisites_label(requisites, bank_name),
                callback_data=RequisitesCallback(
                    action="set_default", requisites_id=requisites.id or 0
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=RequisitesCallback(
                    action="delete", requisites_id=requisites.id or 0
                ).pack(),
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text=REQUISITES_ADD_BUTTON_TEXT,
            callback_data=RequisitesCallback(action="add").pack(),
        )
    )
    return builder.as_markup()


def get_application_requisites_keyboard(
    application_id: int, requisites_list: list[UserRequisites], banks_by_id: dict[int, str]
) -> InlineKeyboardMarkup:
    """Формирует клавиатуру выбора реквизитов для конкретной заявки.

    Args:
        application_id: Внутренний идентификатор заявки.
        requisites_list: Сохранённые наборы реквизитов пользователя.
        banks_by_id: Отображение идентификатора банка в его название.

    Returns:
        Инлайн-клавиатура с кнопкой на каждый сохранённый набор реквизитов
        и кнопкой добавления нового набора.
    """
    builder = InlineKeyboardBuilder()
    for requisites in requisites_list:
        bank_name = banks_by_id.get(requisites.bank_id, "Банк")
        builder.button(
            text=format_requisites_label(requisites, bank_name),
            callback_data=ApplicationRequisitesCallback(
                action="select",
                application_id=application_id,
                requisites_id=requisites.id or 0,
            ).pack(),
        )
    builder.button(
        text="➕ Указать новые реквизиты",
        callback_data=ApplicationRequisitesCallback(
            action="add_new", application_id=application_id
        ).pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_bank_selection_keyboard(banks: list[Bank]) -> InlineKeyboardMarkup:
    """Формирует клавиатуру выбора банка получателя.

    Args:
        banks: Список активных банков, доступных для выбора.

    Returns:
        Инлайн-клавиатура с кнопкой на каждый банк.
    """
    builder = InlineKeyboardBuilder()
    for bank in banks:
        builder.button(
            text=bank.name, callback_data=BankSelectCallback(bank_id=bank.id or 0).pack()
        )
    builder.adjust(1)
    return builder.as_markup()
