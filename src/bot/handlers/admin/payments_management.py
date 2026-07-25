"""Обработчики административного управления выплатами по заявкам."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from src.application.dto.payment_dto import MarkPaymentPaidDTO
from src.application.services.application_service import ApplicationService
from src.application.services.payment_service import PaymentService
from src.application.services.product_service import ProductService
from src.application.services.user_service import UserService
from src.bot.keyboards.admin.main_menu import ADMIN_MENU_PAYMENTS
from src.bot.keyboards.admin.payments import AdminPaymentsCallback, get_admin_payments_list_keyboard
from src.bot.texts.admin_texts import (
    ADMIN_PAYMENTS_EMPTY_TEXT,
    ADMIN_PAYMENTS_HEADER_TEXT,
    PAYMENT_MARKED_PAID_ADMIN_TEXT,
    PAYMENT_NOT_FOUND_ADMIN_TEXT,
    format_admin_payment_list_item,
)
from src.bot.texts.user_texts import format_payment_received_notification
from src.domain.entities.admin import Admin
from src.domain.exceptions.application_exceptions import (
    ApplicationNotFoundError,
    PaymentAlreadyPaidError,
)
from src.domain.exceptions.base import EntityNotFoundError
from src.domain.exceptions.product_exceptions import ProductNotFoundError

logger = logging.getLogger(__name__)

router = Router(name="admin_payments")

_PAGE_SIZE = 5


async def _build_payments_page(
    payment_service: PaymentService,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
    page: int,
) -> tuple[str, InlineKeyboardMarkup]:
    """Формирует текст и клавиатуру страницы списка выплат, ожидающих исполнения.

    Args:
        payment_service: Сервис выплат.
        application_service: Сервис заявок.
        user_service: Сервис пользователей.
        product_service: Сервис товаров каталога.
        page: Номер запрашиваемой страницы (с нуля).

    Returns:
        Кортеж из текста сообщения и инлайн-клавиатуры списка выплат.
    """
    offset = page * _PAGE_SIZE
    payments = await payment_service.list_pending_payments(limit=_PAGE_SIZE + 1, offset=offset)
    has_next_page = len(payments) > _PAGE_SIZE
    payments = payments[:_PAGE_SIZE]

    text = ADMIN_PAYMENTS_HEADER_TEXT
    if not payments and page == 0:
        text = f"{ADMIN_PAYMENTS_HEADER_TEXT}\n\n{ADMIN_PAYMENTS_EMPTY_TEXT}"

    items: list[tuple[int, str]] = []
    for payment in payments:
        try:
            application = await application_service.get_application(payment.application_id)
        except ApplicationNotFoundError:
            continue

        try:
            user = await user_service.get_by_id(application.user_id)
            user_label = user.full_name
        except EntityNotFoundError:
            user_label = f"пользователь #{application.user_id}"

        try:
            product = await product_service.get_product(application.product_id)
            product_title = product.title
        except ProductNotFoundError:
            product_title = f"товар #{application.product_id}"

        items.append(
            (
                payment.application_id,
                format_admin_payment_list_item(
                    payment.application_id, user_label, product_title, str(payment.amount)
                ),
            )
        )

    keyboard = get_admin_payments_list_keyboard(items, page, has_next_page)
    return text, keyboard


@router.message(F.text == ADMIN_MENU_PAYMENTS)
async def handle_payments_menu(
    message: Message,
    payment_service: PaymentService,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Показывает первую страницу списка выплат, ожидающих исполнения.

    Args:
        message: Входящее сообщение с текстом кнопки «💰 Выплаты».
        payment_service: Сервис выплат, внедряемый `ServicesMiddleware`.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_payments_page(
        payment_service, application_service, user_service, product_service, page=0
    )
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(AdminPaymentsCallback.filter(F.action == "list"))
async def handle_payments_page(
    callback: CallbackQuery,
    callback_data: AdminPaymentsCallback,
    payment_service: PaymentService,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Показывает запрошенную страницу списка выплат.

    Args:
        callback: Callback-запрос навигации по страницам.
        callback_data: Разобранные данные callback'а с номером страницы.
        payment_service: Сервис выплат, внедряемый `ServicesMiddleware`.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_payments_page(
        payment_service, application_service, user_service, product_service, callback_data.page
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(AdminPaymentsCallback.filter(F.action == "mark_paid"))
async def handle_mark_payment_paid(
    callback: CallbackQuery,
    callback_data: AdminPaymentsCallback,
    current_admin: Admin,
    payment_service: PaymentService,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Отмечает выплату произведённой и уведомляет пользователя.

    Args:
        callback: Callback-запрос нажатия на строку выплаты.
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        current_admin: Доменная сущность текущего администратора.
        payment_service: Сервис выплат, внедряемый `ServicesMiddleware`.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert current_admin.id is not None
    try:
        await payment_service.mark_application_paid(
            MarkPaymentPaidDTO(
                application_id=callback_data.application_id, admin_id=current_admin.id
            )
        )
    except (EntityNotFoundError, ApplicationNotFoundError, PaymentAlreadyPaidError):
        await callback.answer(PAYMENT_NOT_FOUND_ADMIN_TEXT, show_alert=True)
        return

    try:
        application = await application_service.get_application(callback_data.application_id)
        user = await user_service.get_by_id(application.user_id)
        await callback.bot.send_message(
            chat_id=user.telegram_id,
            text=format_payment_received_notification(callback_data.application_id),
        )
    except (ApplicationNotFoundError, EntityNotFoundError):
        logger.warning(
            "Не удалось найти заявку/пользователя для уведомления о выплате id=%s",
            callback_data.application_id,
        )
    except TelegramAPIError:
        logger.warning(
            "Не удалось уведомить пользователя о выплате по заявке id=%s",
            callback_data.application_id,
        )

    await callback.answer(PAYMENT_MARKED_PAID_ADMIN_TEXT, show_alert=True)
    if isinstance(callback.message, Message):
        text, keyboard = await _build_payments_page(
            payment_service, application_service, user_service, product_service, callback_data.page
        )
        await callback.message.edit_text(text, reply_markup=keyboard)
