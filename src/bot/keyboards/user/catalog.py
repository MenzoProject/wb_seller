"""Клавиатуры и callback-фабрика для навигации по каталогу товаров."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.texts.user_texts import format_product_catalog_item
from src.domain.entities.product import Product


class CatalogCallback(CallbackData, prefix="catalog"):
    """Данные callback-кнопок навигации по каталогу и карточке товара.

    Attributes:
        action: Действие: 'list' — показать страницу списка каталога,
            'open' — открыть карточку конкретного товара, 'order' —
            оформить заявку на товар.
        product_id: Идентификатор товара (для действий 'open' и 'order').
        page: Номер страницы каталога (с нуля), к которой относится действие.
    """

    action: str
    product_id: int = 0
    page: int = 0


def get_catalog_list_keyboard(
    products: list[Product], page: int, has_next_page: bool
) -> InlineKeyboardMarkup:
    """Формирует клавиатуру списка товаров каталога с пагинацией.

    Args:
        products: Товары, отображаемые на текущей странице каталога.
        page: Номер текущей страницы (с нуля).
        has_next_page: Есть ли следующая страница товаров.

    Returns:
        Инлайн-клавиатура с кнопкой на каждый товар и навигацией по страницам.
    """
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=format_product_catalog_item(product),
            callback_data=CatalogCallback(
                action="open", product_id=product.id or 0, page=page
            ).pack(),
        )
    builder.adjust(1)

    navigation_buttons: list[InlineKeyboardButton] = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=CatalogCallback(action="list", page=page - 1).pack(),
            )
        )
    if has_next_page:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=CatalogCallback(action="list", page=page + 1).pack(),
            )
        )
    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


def get_product_card_keyboard(product_id: int, page: int) -> InlineKeyboardMarkup:
    """Формирует клавиатуру карточки товара с кнопкой оформления заявки.

    Args:
        product_id: Внутренний идентификатор товара.
        page: Номер страницы каталога, с которой была открыта карточка
            (используется для корректного возврата назад).

    Returns:
        Инлайн-клавиатура с кнопками «Оформить заявку» и «К каталогу».
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Оформить заявку",
        callback_data=CatalogCallback(action="order", product_id=product_id, page=page).pack(),
    )
    builder.button(
        text="⬅️ К каталогу",
        callback_data=CatalogCallback(action="list", page=page).pack(),
    )
    builder.adjust(1)
    return builder.as_markup()
