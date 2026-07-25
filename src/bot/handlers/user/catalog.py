"""Обработчики каталога товаров: список, карточка товара, начало оформления заявки."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from src.application.dto.application_dto import CreateApplicationDTO
from src.application.services.application_service import ApplicationService
from src.application.services.product_service import ProductService
from src.bot.keyboards.user.application_flow import get_cancel_application_keyboard
from src.bot.keyboards.user.catalog import (
    CatalogCallback,
    get_catalog_list_keyboard,
    get_product_card_keyboard,
)
from src.bot.keyboards.user.main_menu import MENU_CATALOG
from src.bot.states.user_states import ApplicationFlowStates
from src.bot.texts.user_texts import (
    ASK_ARTICLE_TEXT,
    CATALOG_EMPTY_TEXT,
    CATALOG_HEADER_TEXT,
    ORDER_ALREADY_ACTIVE_TEXT,
    ORDER_GENERIC_ERROR_TEXT,
    ORDER_OUT_OF_STOCK_TEXT,
    ORDER_UNAVAILABLE_TEXT,
    format_product_card_text,
)
from src.domain.entities.user import User
from src.domain.exceptions.application_exceptions import ApplicationAlreadyActiveError
from src.domain.exceptions.product_exceptions import (
    ProductNotFoundError,
    ProductOutOfStockError,
    ProductUnavailableError,
)

logger = logging.getLogger(__name__)

router = Router(name="user_catalog")

_PAGE_SIZE = 5


async def _build_catalog_page(
    product_service: ProductService, page: int
) -> tuple[str, InlineKeyboardMarkup | None]:
    """Формирует текст и клавиатуру страницы каталога.

    Args:
        product_service: Сервис товаров каталога.
        page: Номер запрашиваемой страницы (с нуля).

    Returns:
        Кортеж из текста сообщения и клавиатуры (или None, если каталог пуст).
    """
    offset = page * _PAGE_SIZE
    products = await product_service.list_catalog(limit=_PAGE_SIZE + 1, offset=offset)
    has_next_page = len(products) > _PAGE_SIZE
    products = products[:_PAGE_SIZE]

    if not products:
        return CATALOG_EMPTY_TEXT, None

    keyboard = get_catalog_list_keyboard(products, page, has_next_page)
    return CATALOG_HEADER_TEXT, keyboard


@router.message(F.text == MENU_CATALOG)
async def handle_catalog_menu(message: Message, product_service: ProductService) -> None:
    """Показывает первую страницу каталога по нажатию кнопки главного меню.

    Args:
        message: Входящее сообщение с текстом кнопки «📦 Каталог».
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_catalog_page(product_service, page=0)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(CatalogCallback.filter(F.action == "list"))
async def handle_catalog_page(
    callback: CallbackQuery, callback_data: CatalogCallback, product_service: ProductService
) -> None:
    """Показывает запрошенную страницу каталога (пагинация).

    Args:
        callback: Callback-запрос нажатия кнопки навигации.
        callback_data: Разобранные данные callback'а с номером страницы.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_catalog_page(product_service, page=callback_data.page)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(CatalogCallback.filter(F.action == "open"))
async def handle_open_product(
    callback: CallbackQuery, callback_data: CatalogCallback, product_service: ProductService
) -> None:
    """Показывает подробную карточку выбранного товара.

    Args:
        callback: Callback-запрос открытия карточки товара.
        callback_data: Разобранные данные callback'а с идентификатором товара.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    try:
        product = await product_service.get_product(callback_data.product_id)
    except ProductNotFoundError:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            format_product_card_text(product),
            reply_markup=get_product_card_keyboard(callback_data.product_id, callback_data.page),
        )
    await callback.answer()


@router.callback_query(CatalogCallback.filter(F.action == "order"))
async def handle_order_product(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    current_user: User,
    application_service: ApplicationService,
    state: FSMContext,
) -> None:
    """Создаёт заявку на выбранный товар и запускает FSM оформления заявки.

    Args:
        callback: Callback-запрос нажатия кнопки «Оформить заявку».
        callback_data: Разобранные данные callback'а с идентификатором товара.
        current_user: Доменная сущность текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        state: Контекст FSM текущего пользователя.
    """
    assert current_user.id is not None

    try:
        application = await application_service.create_application(
            CreateApplicationDTO(user_id=current_user.id, product_id=callback_data.product_id)
        )
    except ApplicationAlreadyActiveError:
        await callback.answer(ORDER_ALREADY_ACTIVE_TEXT, show_alert=True)
        return
    except ProductOutOfStockError:
        await callback.answer(ORDER_OUT_OF_STOCK_TEXT, show_alert=True)
        return
    except ProductUnavailableError:
        await callback.answer(ORDER_UNAVAILABLE_TEXT, show_alert=True)
        return
    except ProductNotFoundError:
        await callback.answer("Товар не найден.", show_alert=True)
        return
    except Exception:
        logger.exception("Ошибка при создании заявки пользователем id=%s", current_user.id)
        await callback.answer(ORDER_GENERIC_ERROR_TEXT, show_alert=True)
        return

    assert application.id is not None
    await state.set_state(ApplicationFlowStates.waiting_article)
    await state.update_data(application_id=application.id)

    if isinstance(callback.message, Message):
        await callback.message.answer(
            ASK_ARTICLE_TEXT,
            reply_markup=get_cancel_application_keyboard(application.id),
        )
    await callback.answer()
