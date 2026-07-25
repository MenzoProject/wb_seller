"""Обработчики административного управления товарами каталога.

Содержит: список и карточку товара с быстрыми действиями (скрыть/показать,
удалить, изменить остаток) и пошаговый мастер создания/редактирования
товара (`ProductFormStates`). Мастер используется для обоих сценариев —
режим определяется наличием `product_id` в данных FSM.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from src.application.dto.product_dto import ProductCreateDTO, ProductUpdateDTO
from src.application.services.product_service import ProductService
from src.bot.keyboards.admin.main_menu import (
    ADMIN_MENU_BUTTON_TEXTS,
    ADMIN_MENU_PRODUCTS,
    get_admin_main_menu_keyboard,
)
from src.bot.keyboards.admin.products import (
    AdminProductsCallback,
    ProductPhotoSkipCallback,
    YesNoCallback,
    get_admin_product_card_keyboard,
    get_admin_products_list_keyboard,
    get_photo_step_keyboard,
    get_yes_no_keyboard,
)
from src.bot.states.admin_states import ProductFormStates, ProductSlotsChangeStates
from src.bot.texts.admin_texts import (
    ADMIN_PRODUCTS_EMPTY_TEXT,
    ADMIN_PRODUCTS_HEADER_TEXT,
    ASK_NEW_SLOTS_TEXT,
    ASK_PRODUCT_CASHBACK_TEXT,
    ASK_PRODUCT_DESCRIPTION_TEXT,
    ASK_PRODUCT_INSTRUCTION_TEXT,
    ASK_PRODUCT_PAYOUT_DAYS_TEXT,
    ASK_PRODUCT_PHOTO_TEXT,
    ASK_PRODUCT_PRICE_TEXT,
    ASK_PRODUCT_RECEIPT_REQUIRED_TEXT,
    ASK_PRODUCT_REVIEW_REQUIRED_TEXT,
    ASK_PRODUCT_SLOTS_TEXT,
    ASK_PRODUCT_TITLE_TEXT,
    ASK_PRODUCT_URL_TEXT,
    PRODUCT_CASHBACK_INVALID_TEXT,
    PRODUCT_CREATED_TEXT,
    PRODUCT_DELETED_TEXT,
    PRODUCT_DESCRIPTION_EMPTY_TEXT,
    PRODUCT_HIDDEN_TEXT,
    PRODUCT_INSTRUCTION_EMPTY_TEXT,
    PRODUCT_NOT_FOUND_TEXT,
    PRODUCT_PAYOUT_DAYS_INVALID_TEXT,
    PRODUCT_PHOTO_INVALID_TEXT,
    PRODUCT_PRICE_INVALID_TEXT,
    PRODUCT_SLOTS_INVALID_TEXT,
    PRODUCT_SLOTS_UPDATED_TEXT,
    PRODUCT_TITLE_EMPTY_TEXT,
    PRODUCT_UNHIDDEN_TEXT,
    PRODUCT_UPDATED_TEXT,
    PRODUCT_URL_EMPTY_TEXT,
    format_admin_product_card,
)
from src.domain.entities.admin import Admin
from src.domain.exceptions.product_exceptions import ProductNotFoundError, ProductValidationError

router = Router(name="admin_products")

_PAGE_SIZE = 5


async def _build_admin_products_page(
    product_service: ProductService, page: int
) -> tuple[str, InlineKeyboardMarkup]:
    """Формирует текст и клавиатуру страницы списка товаров для администратора.

    Args:
        product_service: Сервис товаров каталога.
        page: Номер запрашиваемой страницы (с нуля).

    Returns:
        Кортеж из текста сообщения и клавиатуры списка товаров.
    """
    offset = page * _PAGE_SIZE
    products = await product_service.list_admin_products(
        include_hidden=True, include_deleted=False, limit=_PAGE_SIZE + 1, offset=offset
    )
    has_next_page = len(products) > _PAGE_SIZE
    products = products[:_PAGE_SIZE]

    text = ADMIN_PRODUCTS_HEADER_TEXT
    if not products and page == 0:
        text = f"{ADMIN_PRODUCTS_HEADER_TEXT}\n\n{ADMIN_PRODUCTS_EMPTY_TEXT}"

    keyboard = get_admin_products_list_keyboard(products, page, has_next_page)
    return text, keyboard


@router.message(F.text == ADMIN_MENU_PRODUCTS)
async def handle_products_menu(message: Message, product_service: ProductService) -> None:
    """Показывает первую страницу списка товаров по нажатию кнопки «📦 Товары».

    Args:
        message: Входящее сообщение с текстом кнопки «📦 Товары».
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_admin_products_page(product_service, page=0)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(AdminProductsCallback.filter(F.action == "list"))
async def handle_products_page(
    callback: CallbackQuery, callback_data: AdminProductsCallback, product_service: ProductService
) -> None:
    """Показывает запрошенную страницу списка товаров.

    Args:
        callback: Callback-запрос навигации по страницам.
        callback_data: Разобранные данные callback'а с номером страницы.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_admin_products_page(product_service, page=callback_data.page)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(AdminProductsCallback.filter(F.action == "open"))
async def handle_open_product_card(
    callback: CallbackQuery, callback_data: AdminProductsCallback, product_service: ProductService
) -> None:
    """Показывает подробную карточку товара с кнопками управления.

    Args:
        callback: Callback-запрос открытия карточки товара.
        callback_data: Разобранные данные callback'а с идентификатором товара.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    try:
        product = await product_service.get_product(callback_data.product_id)
    except ProductNotFoundError:
        await callback.answer(PRODUCT_NOT_FOUND_TEXT, show_alert=True)
        return

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            format_admin_product_card(product),
            reply_markup=get_admin_product_card_keyboard(product, callback_data.page),
        )
    await callback.answer()


async def _refresh_product_card(
    callback: CallbackQuery, product_id: int, page: int, product_service: ProductService
) -> None:
    """Перерисовывает карточку товара после изменения его состояния.

    Args:
        callback: Callback-запрос, инициировавший изменение.
        product_id: Внутренний идентификатор товара.
        page: Номер страницы списка, с которой была открыта карточка.
        product_service: Сервис товаров каталога.
    """
    product = await product_service.get_product(product_id)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            format_admin_product_card(product),
            reply_markup=get_admin_product_card_keyboard(product, page),
        )


@router.callback_query(AdminProductsCallback.filter(F.action == "hide"))
async def handle_hide_product(
    callback: CallbackQuery,
    callback_data: AdminProductsCallback,
    current_admin: Admin,
    product_service: ProductService,
) -> None:
    """Скрывает товар из каталога.

    Args:
        callback: Callback-запрос нажатия кнопки «🙈 Скрыть».
        callback_data: Разобранные данные callback'а с идентификатором товара.
        current_admin: Доменная сущность текущего администратора.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert current_admin.id is not None
    try:
        await product_service.hide_product(callback_data.product_id, current_admin.id)
    except ProductNotFoundError:
        await callback.answer(PRODUCT_NOT_FOUND_TEXT, show_alert=True)
        return

    await callback.answer(PRODUCT_HIDDEN_TEXT)
    await _refresh_product_card(
        callback, callback_data.product_id, callback_data.page, product_service
    )


@router.callback_query(AdminProductsCallback.filter(F.action == "unhide"))
async def handle_unhide_product(
    callback: CallbackQuery,
    callback_data: AdminProductsCallback,
    current_admin: Admin,
    product_service: ProductService,
) -> None:
    """Возвращает товар в каталог.

    Args:
        callback: Callback-запрос нажатия кнопки «👁 Показать».
        callback_data: Разобранные данные callback'а с идентификатором товара.
        current_admin: Доменная сущность текущего администратора.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert current_admin.id is not None
    try:
        await product_service.unhide_product(callback_data.product_id, current_admin.id)
    except ProductNotFoundError:
        await callback.answer(PRODUCT_NOT_FOUND_TEXT, show_alert=True)
        return

    await callback.answer(PRODUCT_UNHIDDEN_TEXT)
    await _refresh_product_card(
        callback, callback_data.product_id, callback_data.page, product_service
    )


@router.callback_query(AdminProductsCallback.filter(F.action == "delete"))
async def handle_delete_product(
    callback: CallbackQuery,
    callback_data: AdminProductsCallback,
    current_admin: Admin,
    product_service: ProductService,
) -> None:
    """Мягко удаляет товар из каталога.

    Args:
        callback: Callback-запрос нажатия кнопки «🗑 Удалить».
        callback_data: Разобранные данные callback'а с идентификатором товара.
        current_admin: Доменная сущность текущего администратора.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert current_admin.id is not None
    try:
        await product_service.delete_product(callback_data.product_id, current_admin.id)
    except ProductNotFoundError:
        await callback.answer(PRODUCT_NOT_FOUND_TEXT, show_alert=True)
        return

    await callback.answer(PRODUCT_DELETED_TEXT)
    text, keyboard = await _build_admin_products_page(product_service, page=callback_data.page)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(AdminProductsCallback.filter(F.action == "change_slots"))
async def handle_start_change_slots(
    callback: CallbackQuery, callback_data: AdminProductsCallback, state: FSMContext
) -> None:
    """Запускает FSM изменения количества доступных заявок товара.

    Args:
        callback: Callback-запрос нажатия кнопки «📦 Изменить остаток».
        callback_data: Разобранные данные callback'а с идентификатором товара.
        state: Контекст FSM текущего администратора.
    """
    await state.set_state(ProductSlotsChangeStates.waiting_new_slots)
    await state.update_data(product_id=callback_data.product_id, page=callback_data.page)

    if isinstance(callback.message, Message):
        await callback.message.answer(ASK_NEW_SLOTS_TEXT)
    await callback.answer()


@router.message(ProductSlotsChangeStates.waiting_new_slots, F.text)
async def handle_new_slots_input(
    message: Message,
    state: FSMContext,
    current_admin: Admin,
    product_service: ProductService,
) -> None:
    """Применяет новое количество доступных заявок товара.

    Args:
        message: Входящее сообщение с новым количеством слотов.
        state: Контекст FSM текущего администратора.
        current_admin: Доменная сущность текущего администратора.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert current_admin.id is not None
    try:
        new_slots = int((message.text or "").strip())
    except ValueError:
        await message.answer(PRODUCT_SLOTS_INVALID_TEXT)
        return
    if new_slots < 0:
        await message.answer(PRODUCT_SLOTS_INVALID_TEXT)
        return

    data = await state.get_data()
    product_id: int = data["product_id"]
    page: int = data["page"]
    await state.clear()

    try:
        product = await product_service.change_available_slots(
            product_id, new_slots, current_admin.id
        )
    except ProductNotFoundError:
        await message.answer(PRODUCT_NOT_FOUND_TEXT)
        return
    except ProductValidationError:
        await message.answer(PRODUCT_SLOTS_INVALID_TEXT)
        return

    await message.answer(PRODUCT_SLOTS_UPDATED_TEXT)
    await message.answer(
        format_admin_product_card(product),
        reply_markup=get_admin_product_card_keyboard(product, page),
    )


@router.message(ProductSlotsChangeStates.waiting_new_slots)
async def handle_new_slots_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания нового количества слотов.

    Args:
        message: Входящее сообщение, не содержащее корректного числа.
    """
    await message.answer(PRODUCT_SLOTS_INVALID_TEXT)


@router.message(
    StateFilter(ProductFormStates, ProductSlotsChangeStates), F.text.in_(ADMIN_MENU_BUTTON_TEXTS)
)
async def handle_menu_interrupts_admin_flow(message: Message, state: FSMContext) -> None:
    """Прерывает мастер создания/редактирования товара при переходе в другой раздел меню.

    Args:
        message: Входящее сообщение с текстом кнопки главного меню.
        state: Контекст FSM текущего администратора.
    """
    await state.clear()
    await message.answer(
        "Действие прервано. Нажмите на нужный раздел ещё раз.",
        reply_markup=get_admin_main_menu_keyboard(),
    )


@router.callback_query(AdminProductsCallback.filter(F.action == "create"))
async def handle_start_create_product(callback: CallbackQuery, state: FSMContext) -> None:
    """Запускает мастер создания нового товара.

    Args:
        callback: Callback-запрос нажатия кнопки «➕ Добавить товар».
        state: Контекст FSM текущего администратора.
    """
    await state.set_state(ProductFormStates.waiting_title)
    await state.update_data(product_id=None, page=0)

    if isinstance(callback.message, Message):
        await callback.message.answer(ASK_PRODUCT_TITLE_TEXT)
    await callback.answer()


@router.callback_query(AdminProductsCallback.filter(F.action == "edit"))
async def handle_start_edit_product(
    callback: CallbackQuery,
    callback_data: AdminProductsCallback,
    state: FSMContext,
    product_service: ProductService,
) -> None:
    """Запускает мастер редактирования существующего товара.

    Показывает текущую карточку товара для справки, после чего запрашивает
    все поля заново по тому же сценарию, что и при создании товара.

    Args:
        callback: Callback-запрос нажатия кнопки «✏️ Редактировать».
        callback_data: Разобранные данные callback'а с идентификатором товара.
        state: Контекст FSM текущего администратора.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    try:
        product = await product_service.get_product(callback_data.product_id)
    except ProductNotFoundError:
        await callback.answer(PRODUCT_NOT_FOUND_TEXT, show_alert=True)
        return

    await state.set_state(ProductFormStates.waiting_title)
    await state.update_data(product_id=product.id, page=callback_data.page)

    if isinstance(callback.message, Message):
        await callback.message.answer(
            f"{format_admin_product_card(product)}\n\n"
            f"Начинаем редактирование — все поля нужно будет ввести заново.\n\n"
            f"{ASK_PRODUCT_TITLE_TEXT}"
        )
    await callback.answer()


@router.message(ProductFormStates.waiting_title, F.text)
async def handle_form_title(message: Message, state: FSMContext) -> None:
    """Фиксирует название товара и переходит к запросу описания.

    Args:
        message: Входящее сообщение с названием товара.
        state: Контекст FSM текущего администратора.
    """
    title = (message.text or "").strip()
    if not title:
        await message.answer(PRODUCT_TITLE_EMPTY_TEXT)
        return

    await state.update_data(title=title)
    await state.set_state(ProductFormStates.waiting_description)
    await message.answer(ASK_PRODUCT_DESCRIPTION_TEXT)


@router.message(ProductFormStates.waiting_title)
async def handle_form_title_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания названия товара."""
    await message.answer(PRODUCT_TITLE_EMPTY_TEXT)


@router.message(ProductFormStates.waiting_description, F.text)
async def handle_form_description(message: Message, state: FSMContext) -> None:
    """Фиксирует описание товара и переходит к запросу цены.

    Args:
        message: Входящее сообщение с описанием товара.
        state: Контекст FSM текущего администратора.
    """
    description = (message.text or "").strip()
    if not description:
        await message.answer(PRODUCT_DESCRIPTION_EMPTY_TEXT)
        return

    await state.update_data(description=description)
    await state.set_state(ProductFormStates.waiting_price)
    await message.answer(ASK_PRODUCT_PRICE_TEXT)


@router.message(ProductFormStates.waiting_description)
async def handle_form_description_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания описания товара."""
    await message.answer(PRODUCT_DESCRIPTION_EMPTY_TEXT)


def _parse_decimal(raw_value: str) -> Decimal | None:
    """Пытается разобрать введённую администратором строку как денежную сумму.

    Args:
        raw_value: Исходный текст, введённый администратором.

    Returns:
        Разобранное неотрицательное значение `Decimal`, либо None при ошибке.
    """
    try:
        value = Decimal(raw_value.strip().replace(",", "."))
    except InvalidOperation:
        return None
    if value < 0:
        return None
    return value


@router.message(ProductFormStates.waiting_price, F.text)
async def handle_form_price(message: Message, state: FSMContext) -> None:
    """Фиксирует цену товара и переходит к запросу суммы кэшбэка.

    Args:
        message: Входящее сообщение с ценой товара.
        state: Контекст FSM текущего администратора.
    """
    price = _parse_decimal(message.text or "")
    if price is None:
        await message.answer(PRODUCT_PRICE_INVALID_TEXT)
        return

    await state.update_data(price=str(price))
    await state.set_state(ProductFormStates.waiting_cashback_amount)
    await message.answer(ASK_PRODUCT_CASHBACK_TEXT)


@router.message(ProductFormStates.waiting_price)
async def handle_form_price_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания цены товара."""
    await message.answer(PRODUCT_PRICE_INVALID_TEXT)


@router.message(ProductFormStates.waiting_cashback_amount, F.text)
async def handle_form_cashback(message: Message, state: FSMContext) -> None:
    """Фиксирует сумму кэшбэка и переходит к запросу срока выплаты.

    Args:
        message: Входящее сообщение с суммой кэшбэка.
        state: Контекст FSM текущего администратора.
    """
    cashback_amount = _parse_decimal(message.text or "")
    if cashback_amount is None:
        await message.answer(PRODUCT_CASHBACK_INVALID_TEXT)
        return

    await state.update_data(cashback_amount=str(cashback_amount))
    await state.set_state(ProductFormStates.waiting_payout_days)
    await message.answer(ASK_PRODUCT_PAYOUT_DAYS_TEXT)


@router.message(ProductFormStates.waiting_cashback_amount)
async def handle_form_cashback_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания суммы кэшбэка."""
    await message.answer(PRODUCT_CASHBACK_INVALID_TEXT)


@router.message(ProductFormStates.waiting_payout_days, F.text)
async def handle_form_payout_days(message: Message, state: FSMContext) -> None:
    """Фиксирует срок выплаты и переходит к вопросу об обязательности отзыва.

    Args:
        message: Входящее сообщение со сроком выплаты в днях.
        state: Контекст FSM текущего администратора.
    """
    try:
        payout_days = int((message.text or "").strip())
    except ValueError:
        await message.answer(PRODUCT_PAYOUT_DAYS_INVALID_TEXT)
        return
    if payout_days <= 0:
        await message.answer(PRODUCT_PAYOUT_DAYS_INVALID_TEXT)
        return

    await state.update_data(payout_days=str(payout_days))
    await state.set_state(ProductFormStates.waiting_review_required)
    await message.answer(ASK_PRODUCT_REVIEW_REQUIRED_TEXT, reply_markup=get_yes_no_keyboard())


@router.message(ProductFormStates.waiting_payout_days)
async def handle_form_payout_days_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания срока выплаты."""
    await message.answer(PRODUCT_PAYOUT_DAYS_INVALID_TEXT)


@router.callback_query(ProductFormStates.waiting_review_required, YesNoCallback.filter())
async def handle_form_review_required(
    callback: CallbackQuery, callback_data: YesNoCallback, state: FSMContext
) -> None:
    """Фиксирует требование отзыва и переходит к вопросу об обязательности чека.

    Args:
        callback: Callback-запрос выбора «Да» или «Нет».
        callback_data: Разобранные данные callback'а с выбранным значением.
        state: Контекст FSM текущего администратора.
    """
    await state.update_data(review_required=callback_data.value)
    await state.set_state(ProductFormStates.waiting_receipt_required)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            ASK_PRODUCT_RECEIPT_REQUIRED_TEXT, reply_markup=get_yes_no_keyboard()
        )
    await callback.answer()


@router.callback_query(ProductFormStates.waiting_receipt_required, YesNoCallback.filter())
async def handle_form_receipt_required(
    callback: CallbackQuery, callback_data: YesNoCallback, state: FSMContext
) -> None:
    """Фиксирует требование чека и переходит к запросу ссылки на товар.

    Args:
        callback: Callback-запрос выбора «Да» или «Нет».
        callback_data: Разобранные данные callback'а с выбранным значением.
        state: Контекст FSM текущего администратора.
    """
    await state.update_data(receipt_required=callback_data.value)
    await state.set_state(ProductFormStates.waiting_product_url)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(ASK_PRODUCT_URL_TEXT)
    await callback.answer()


@router.message(ProductFormStates.waiting_product_url, F.text)
async def handle_form_url(message: Message, state: FSMContext) -> None:
    """Фиксирует ссылку на товар и переходит к запросу инструкции.

    Args:
        message: Входящее сообщение со ссылкой на товар.
        state: Контекст FSM текущего администратора.
    """
    product_url = (message.text or "").strip()
    if not product_url:
        await message.answer(PRODUCT_URL_EMPTY_TEXT)
        return

    await state.update_data(product_url=product_url)
    await state.set_state(ProductFormStates.waiting_instruction_text)
    await message.answer(ASK_PRODUCT_INSTRUCTION_TEXT)


@router.message(ProductFormStates.waiting_product_url)
async def handle_form_url_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания ссылки на товар."""
    await message.answer(PRODUCT_URL_EMPTY_TEXT)


@router.message(ProductFormStates.waiting_instruction_text, F.text)
async def handle_form_instruction(message: Message, state: FSMContext) -> None:
    """Фиксирует текст инструкции и переходит к запросу количества доступных заявок.

    Args:
        message: Входящее сообщение с текстом инструкции.
        state: Контекст FSM текущего администратора.
    """
    instruction_text = (message.text or "").strip()
    if not instruction_text:
        await message.answer(PRODUCT_INSTRUCTION_EMPTY_TEXT)
        return

    await state.update_data(instruction_text=instruction_text)
    await state.set_state(ProductFormStates.waiting_available_slots)
    await message.answer(ASK_PRODUCT_SLOTS_TEXT)


@router.message(ProductFormStates.waiting_instruction_text)
async def handle_form_instruction_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания текста инструкции."""
    await message.answer(PRODUCT_INSTRUCTION_EMPTY_TEXT)


@router.message(ProductFormStates.waiting_available_slots, F.text)
async def handle_form_slots(message: Message, state: FSMContext) -> None:
    """Фиксирует количество доступных заявок и переходит к загрузке фотографии.

    Args:
        message: Входящее сообщение с количеством доступных заявок.
        state: Контекст FSM текущего администратора.
    """
    try:
        available_slots = int((message.text or "").strip())
    except ValueError:
        await message.answer(PRODUCT_SLOTS_INVALID_TEXT)
        return
    if available_slots < 0:
        await message.answer(PRODUCT_SLOTS_INVALID_TEXT)
        return

    await state.update_data(available_slots=str(available_slots))
    await state.set_state(ProductFormStates.waiting_photo)
    await message.answer(ASK_PRODUCT_PHOTO_TEXT, reply_markup=get_photo_step_keyboard())


@router.message(ProductFormStates.waiting_available_slots)
async def handle_form_slots_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания количества доступных заявок."""
    await message.answer(PRODUCT_SLOTS_INVALID_TEXT)


async def _finalize_product_form(
    answer_target: Message,
    state: FSMContext,
    current_admin: Admin,
    product_service: ProductService,
    photo_file_id: str | None,
) -> None:
    """Завершает мастер, создавая или обновляя товар по накопленным в FSM данным.

    Args:
        answer_target: Сообщение, в ответ на которое отправляется результат.
        state: Контекст FSM текущего администратора.
        current_admin: Доменная сущность текущего администратора.
        product_service: Сервис товаров каталога.
        photo_file_id: Идентификатор загруженной фотографии товара, либо
            None, если шаг загрузки фотографии был пропущен.
    """
    assert current_admin.id is not None
    data = await state.get_data()
    await state.clear()

    photo_file_ids = [photo_file_id] if photo_file_id is not None else []

    if data.get("product_id") is None:
        created_product = await product_service.create_product(
            ProductCreateDTO(
                title=data["title"],
                description=data["description"],
                price=Decimal(data["price"]),
                cashback_amount=Decimal(data["cashback_amount"]),
                payout_days=int(data["payout_days"]),
                review_required=data["review_required"],
                receipt_required=data["receipt_required"],
                product_url=data["product_url"],
                instruction_text=data["instruction_text"],
                available_slots=int(data["available_slots"]),
                photo_file_ids=photo_file_ids,
                admin_id=current_admin.id,
            )
        )
        await answer_target.answer(PRODUCT_CREATED_TEXT)
        result_product = created_product
        page = 0
    else:
        updated_product = await product_service.update_product(
            ProductUpdateDTO(
                product_id=data["product_id"],
                title=data["title"],
                description=data["description"],
                price=Decimal(data["price"]),
                cashback_amount=Decimal(data["cashback_amount"]),
                payout_days=int(data["payout_days"]),
                review_required=data["review_required"],
                receipt_required=data["receipt_required"],
                product_url=data["product_url"],
                instruction_text=data["instruction_text"],
                available_slots=int(data["available_slots"]),
                photo_file_ids=photo_file_ids,
                admin_id=current_admin.id,
            )
        )
        await answer_target.answer(PRODUCT_UPDATED_TEXT)
        result_product = updated_product
        page = data.get("page", 0)

    await answer_target.answer(
        format_admin_product_card(result_product),
        reply_markup=get_admin_product_card_keyboard(result_product, page),
    )


@router.message(ProductFormStates.waiting_photo, F.photo)
async def handle_form_photo(
    message: Message, state: FSMContext, current_admin: Admin, product_service: ProductService
) -> None:
    """Завершает мастер после получения фотографии товара.

    Args:
        message: Входящее сообщение с фотографией товара.
        state: Контекст FSM текущего администратора.
        current_admin: Доменная сущность текущего администратора.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert message.photo is not None
    file_id = message.photo[-1].file_id
    await _finalize_product_form(message, state, current_admin, product_service, file_id)


@router.callback_query(ProductFormStates.waiting_photo, ProductPhotoSkipCallback.filter())
async def handle_form_photo_skip(
    callback: CallbackQuery,
    state: FSMContext,
    current_admin: Admin,
    product_service: ProductService,
) -> None:
    """Завершает мастер без фотографии товара по нажатию кнопки пропуска.

    Args:
        callback: Callback-запрос нажатия кнопки «⏭ Без фото».
        state: Контекст FSM текущего администратора.
        current_admin: Доменная сущность текущего администратора.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    if isinstance(callback.message, Message):
        await _finalize_product_form(callback.message, state, current_admin, product_service, None)
    await callback.answer()


@router.message(ProductFormStates.waiting_photo)
async def handle_form_photo_invalid(message: Message) -> None:
    """Отвечает на некорректный ввод во время ожидания фотографии товара."""
    await message.answer(PRODUCT_PHOTO_INVALID_TEXT)
