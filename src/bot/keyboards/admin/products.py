"""Клавиатуры и callback-фабрики административного управления товарами."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.texts.admin_texts import (
    ADD_PRODUCT_BUTTON_TEXT,
    NO_BUTTON_TEXT,
    PRODUCT_PHOTO_SKIP_BUTTON_TEXT,
    YES_BUTTON_TEXT,
    format_admin_product_list_item,
)
from src.domain.entities.product import Product


class AdminProductsCallback(CallbackData, prefix="a_prod"):
    """Данные callback-кнопок раздела управления товарами.

    Attributes:
        action: Действие: 'list' — страница списка товаров, 'open' —
            открыть карточку товара, 'create' — начать создание нового
            товара, 'edit' — начать редактирование, 'hide'/'unhide' —
            скрыть/показать, 'delete' — мягко удалить, 'change_slots' —
            изменить количество доступных заявок.
        product_id: Идентификатор товара (для всех действий, кроме 'list' и 'create').
        page: Номер страницы списка, к которой относится действие.
    """

    action: str
    product_id: int = 0
    page: int = 0


class YesNoCallback(CallbackData, prefix="yesno"):
    """Данные callback-кнопки бинарного выбора «Да/Нет» в мастере создания товара.

    Attributes:
        value: Выбранное значение.
    """

    value: bool


class ProductPhotoSkipCallback(CallbackData, prefix="prod_photo_skip"):
    """Данные callback-кнопки пропуска шага загрузки фотографии товара."""


def get_admin_products_list_keyboard(
    products: list[Product], page: int, has_next_page: bool
) -> InlineKeyboardMarkup:
    """Формирует клавиатуру списка товаров для панели администратора с пагинацией.

    Args:
        products: Товары, отображаемые на текущей странице.
        page: Номер текущей страницы (с нуля).
        has_next_page: Есть ли следующая страница товаров.

    Returns:
        Инлайн-клавиатура со списком товаров, навигацией и кнопкой добавления товара.
    """
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=format_admin_product_list_item(product),
            callback_data=AdminProductsCallback(
                action="open", product_id=product.id or 0, page=page
            ).pack(),
        )
    builder.adjust(1)

    navigation_buttons: list[InlineKeyboardButton] = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=AdminProductsCallback(action="list", page=page - 1).pack(),
            )
        )
    if has_next_page:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=AdminProductsCallback(action="list", page=page + 1).pack(),
            )
        )
    if navigation_buttons:
        builder.row(*navigation_buttons)

    builder.row(
        InlineKeyboardButton(
            text=ADD_PRODUCT_BUTTON_TEXT,
            callback_data=AdminProductsCallback(action="create").pack(),
        )
    )
    return builder.as_markup()


def get_admin_product_card_keyboard(product: Product, page: int) -> InlineKeyboardMarkup:
    """Формирует клавиатуру карточки товара с действиями управления.

    Args:
        product: Доменная сущность товара.
        page: Номер страницы списка, с которой была открыта карточка.

    Returns:
        Инлайн-клавиатура с кнопками редактирования, скрытия/показа,
        изменения остатка, удаления и возврата к списку.
    """
    product_id = product.id or 0
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✏️ Редактировать",
        callback_data=AdminProductsCallback(action="edit", product_id=product_id, page=page).pack(),
    )

    if product.is_hidden:
        builder.button(
            text="👁 Показать",
            callback_data=AdminProductsCallback(
                action="unhide", product_id=product_id, page=page
            ).pack(),
        )
    else:
        builder.button(
            text="🙈 Скрыть",
            callback_data=AdminProductsCallback(
                action="hide", product_id=product_id, page=page
            ).pack(),
        )

    builder.button(
        text="📦 Изменить остаток",
        callback_data=AdminProductsCallback(
            action="change_slots", product_id=product_id, page=page
        ).pack(),
    )
    builder.button(
        text="🗑 Удалить",
        callback_data=AdminProductsCallback(
            action="delete", product_id=product_id, page=page
        ).pack(),
    )
    builder.button(
        text="⬅️ К списку",
        callback_data=AdminProductsCallback(action="list", page=page).pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Формирует клавиатуру бинарного выбора «Да/Нет».

    Returns:
        Инлайн-клавиатура с двумя кнопками.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=YES_BUTTON_TEXT, callback_data=YesNoCallback(value=True).pack())
    builder.button(text=NO_BUTTON_TEXT, callback_data=YesNoCallback(value=False).pack())
    builder.adjust(2)
    return builder.as_markup()


def get_photo_step_keyboard() -> InlineKeyboardMarkup:
    """Формирует клавиатуру шага загрузки фотографии с кнопкой пропуска.

    Returns:
        Инлайн-клавиатура с кнопкой «⏭ Без фото».
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=PRODUCT_PHOTO_SKIP_BUTTON_TEXT, callback_data=ProductPhotoSkipCallback().pack()
    )
    return builder.as_markup()
