"""Обработчики административного управления заявками.

Здесь реализована ключевая связка процесса: одобрение заказа
администратором немедленно отправляет пользователю кнопку «✅ Я получил(а)
товар» (см. `handlers/user/application_flow.py`, куда ведёт нажатие этой
кнопки). Запрос повторной отправки скриншота дополнительно программно
переводит FSM пользователя обратно в состояние ожидания фото — это
единственный сценарий в проекте, где администратор напрямую управляет
FSM-состоянием другого пользователя.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from src.application.dto.application_dto import (
    ApproveOrderDTO,
    RejectApplicationDTO,
    RequestOrderScreenshotResendDTO,
)
from src.application.services.application_service import ApplicationService
from src.application.services.product_service import ProductService
from src.application.services.user_service import UserService
from src.bot.keyboards.admin.applications import (
    AdminApplicationsCallback,
    get_admin_application_card_keyboard,
    get_admin_applications_queue_keyboard,
)
from src.bot.keyboards.admin.main_menu import (
    ADMIN_MENU_BUTTON_TEXTS,
    ADMIN_MENU_REQUESTS,
    get_admin_main_menu_keyboard,
)
from src.bot.keyboards.user.application_flow import get_confirm_receive_keyboard
from src.bot.states.admin_states import ApplicationReviewStates
from src.bot.states.user_states import ApplicationFlowStates
from src.bot.texts.admin_texts import (
    ADMIN_APPLICATIONS_EMPTY_TEXT,
    ADMIN_APPLICATIONS_HEADER_TEXT,
    APPLICATION_APPROVED_ADMIN_TEXT,
    APPLICATION_NOT_FOUND_ADMIN_TEXT,
    APPLICATION_REJECTED_ADMIN_TEXT,
    APPLICATION_RESEND_REQUESTED_ADMIN_TEXT,
    ASK_REJECT_REASON_TEXT,
    ASK_RESEND_REASON_TEXT,
    REJECT_REASON_EMPTY_TEXT,
    RESEND_REASON_EMPTY_TEXT,
    format_admin_application_card,
    format_admin_application_list_item,
)
from src.bot.texts.user_texts import (
    ASK_CONFIRM_RECEIVE_TEXT,
    format_order_rejected_notification,
    format_order_resend_requested_notification,
)
from src.domain.entities.admin import Admin
from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.application_exceptions import (
    ApplicationNotFoundError,
    ApplicationRejectionReasonRequiredError,
    InvalidApplicationTransitionError,
)
from src.domain.exceptions.base import EntityNotFoundError
from src.domain.exceptions.product_exceptions import ProductNotFoundError

logger = logging.getLogger(__name__)

router = Router(name="admin_applications")

_PAGE_SIZE = 5


def _build_user_fsm_context(storage: BaseStorage, bot_id: int, user_telegram_id: int) -> FSMContext:
    """Строит контекст FSM конкретного пользователя для программного управления им.

    Args:
        storage: Хранилище FSM-состояний бота.
        bot_id: Идентификатор бота (часть ключа хранилища FSM).
        user_telegram_id: Telegram ID пользователя, чей контекст нужно получить.

    Returns:
        Контекст FSM указанного пользователя в его личном чате с ботом.
    """
    key = StorageKey(bot_id=bot_id, chat_id=user_telegram_id, user_id=user_telegram_id)
    return FSMContext(storage=storage, key=key)


async def _build_applications_queue_page(
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
    page: int,
) -> tuple[str, InlineKeyboardMarkup]:
    """Формирует текст и клавиатуру страницы очереди заявок на проверку.

    Args:
        application_service: Сервис заявок.
        user_service: Сервис пользователей.
        product_service: Сервис товаров каталога.
        page: Номер запрашиваемой страницы (с нуля).

    Returns:
        Кортеж из текста сообщения и инлайн-клавиатуры очереди.
    """
    offset = page * _PAGE_SIZE
    applications = await application_service.list_applications_by_status(
        ApplicationStatus.ORDER_ON_REVIEW, limit=_PAGE_SIZE + 1, offset=offset
    )
    has_next_page = len(applications) > _PAGE_SIZE
    applications = applications[:_PAGE_SIZE]

    text = ADMIN_APPLICATIONS_HEADER_TEXT
    if not applications and page == 0:
        text = f"{ADMIN_APPLICATIONS_HEADER_TEXT}\n\n{ADMIN_APPLICATIONS_EMPTY_TEXT}"

    items: list[tuple[int, str]] = []
    for application in applications:
        assert application.id is not None
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
                application.id,
                format_admin_application_list_item(application.id, user_label, product_title),
            )
        )

    keyboard = get_admin_applications_queue_keyboard(items, page, has_next_page)
    return text, keyboard


@router.message(F.text == ADMIN_MENU_REQUESTS)
async def handle_applications_menu(
    message: Message,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Показывает первую страницу очереди заявок, ожидающих проверки.

    Args:
        message: Входящее сообщение с текстом кнопки «📋 Заявки».
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_applications_queue_page(
        application_service, user_service, product_service, page=0
    )
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(AdminApplicationsCallback.filter(F.action == "queue"))
async def handle_applications_queue_page(
    callback: CallbackQuery,
    callback_data: AdminApplicationsCallback,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Показывает запрошенную страницу очереди заявок.

    Args:
        callback: Callback-запрос навигации по страницам очереди.
        callback_data: Разобранные данные callback'а с номером страницы.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _build_applications_queue_page(
        application_service, user_service, product_service, callback_data.page
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(AdminApplicationsCallback.filter(F.action == "open"))
async def handle_open_application_card(
    callback: CallbackQuery,
    callback_data: AdminApplicationsCallback,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Показывает подробную карточку заявки со скриншотом заказа (если он есть).

    Args:
        callback: Callback-запрос открытия карточки заявки.
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    try:
        application = await application_service.get_application(callback_data.application_id)
    except ApplicationNotFoundError:
        await callback.answer(APPLICATION_NOT_FOUND_ADMIN_TEXT, show_alert=True)
        return

    try:
        user = await user_service.get_by_id(application.user_id)
        user_mention = user.mention
    except EntityNotFoundError:
        user_mention = f"пользователь #{application.user_id}"

    try:
        product = await product_service.get_product(application.product_id)
        product_title = product.title
    except ProductNotFoundError:
        product_title = f"товар #{application.product_id}"

    assert application.id is not None
    card_text = format_admin_application_card(
        application.id,
        user_mention,
        product_title,
        application.article,
        application.order_screenshot_file_id,
    )
    keyboard = get_admin_application_card_keyboard(application.id, callback_data.page)

    if isinstance(callback.message, Message):
        if application.order_screenshot_file_id:
            await callback.message.answer_photo(
                application.order_screenshot_file_id, caption=card_text, reply_markup=keyboard
            )
        else:
            await callback.message.answer(card_text, reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(ApplicationReviewStates), F.text.in_(ADMIN_MENU_BUTTON_TEXTS))
async def handle_menu_interrupts_review_flow(message: Message, state: FSMContext) -> None:
    """Прерывает ввод причины отклонения/повтора при переходе в другой раздел меню.

    Args:
        message: Входящее сообщение с текстом кнопки главного меню.
        state: Контекст FSM текущего администратора.
    """
    await state.clear()
    await message.answer(
        "Действие прервано. Нажмите на нужный раздел ещё раз.",
        reply_markup=get_admin_main_menu_keyboard(),
    )


@router.callback_query(AdminApplicationsCallback.filter(F.action == "approve"))
async def handle_approve_application(
    callback: CallbackQuery,
    callback_data: AdminApplicationsCallback,
    current_admin: Admin,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Одобряет заказ и отправляет пользователю кнопку подтверждения получения товара.

    Args:
        callback: Callback-запрос нажатия кнопки «✅ Одобрить».
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        current_admin: Доменная сущность текущего администратора.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert current_admin.id is not None
    try:
        application = await application_service.approve_order(
            ApproveOrderDTO(
                application_id=callback_data.application_id, admin_id=current_admin.id
            )
        )
    except (ApplicationNotFoundError, InvalidApplicationTransitionError):
        await callback.answer(APPLICATION_NOT_FOUND_ADMIN_TEXT, show_alert=True)
        return

    assert application.id is not None
    try:
        user = await user_service.get_by_id(application.user_id)
        await callback.bot.send_message(
            chat_id=user.telegram_id,
            text=ASK_CONFIRM_RECEIVE_TEXT,
            reply_markup=get_confirm_receive_keyboard(application.id),
        )
    except EntityNotFoundError:
        logger.warning(
            "Пользователь id=%s для заявки id=%s не найден", application.user_id, application.id
        )
    except TelegramAPIError:
        logger.warning(
            "Не удалось уведомить пользователя об одобрении заявки id=%s", application.id
        )

    await callback.answer(APPLICATION_APPROVED_ADMIN_TEXT, show_alert=True)
    if isinstance(callback.message, Message):
        text, keyboard = await _build_applications_queue_page(
            application_service, user_service, product_service, callback_data.page
        )
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(AdminApplicationsCallback.filter(F.action == "reject"))
async def handle_start_reject_application(
    callback: CallbackQuery, callback_data: AdminApplicationsCallback, state: FSMContext
) -> None:
    """Запускает ввод причины отклонения заявки.

    Args:
        callback: Callback-запрос нажатия кнопки «❌ Отклонить».
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        state: Контекст FSM текущего администратора.
    """
    await state.set_state(ApplicationReviewStates.waiting_reject_reason)
    await state.update_data(application_id=callback_data.application_id, page=callback_data.page)

    if isinstance(callback.message, Message):
        await callback.message.answer(ASK_REJECT_REASON_TEXT)
    await callback.answer()


@router.message(ApplicationReviewStates.waiting_reject_reason, F.text)
async def handle_reject_reason_input(
    message: Message,
    state: FSMContext,
    current_admin: Admin,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
) -> None:
    """Отклоняет заявку с указанной причиной и уведомляет пользователя.

    Args:
        message: Входящее сообщение с причиной отклонения.
        state: Контекст FSM текущего администратора.
        current_admin: Доменная сущность текущего администратора.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    reason = (message.text or "").strip()
    if not reason:
        await message.answer(REJECT_REASON_EMPTY_TEXT)
        return

    data = await state.get_data()
    application_id: int = data["application_id"]
    page: int = data["page"]
    await state.clear()

    assert current_admin.id is not None
    try:
        application = await application_service.reject_application(
            RejectApplicationDTO(
                application_id=application_id, admin_id=current_admin.id, reason=reason
            )
        )
    except (
        ApplicationNotFoundError,
        ApplicationRejectionReasonRequiredError,
        InvalidApplicationTransitionError,
    ):
        await message.answer(APPLICATION_NOT_FOUND_ADMIN_TEXT)
        return

    try:
        user = await user_service.get_by_id(application.user_id)
        assert message.bot is not None
        await message.bot.send_message(
            chat_id=user.telegram_id,
            text=format_order_rejected_notification(application_id, reason),
        )
    except EntityNotFoundError:
        logger.warning("Пользователь для заявки id=%s не найден", application_id)
    except TelegramAPIError:
        logger.warning(
            "Не удалось уведомить пользователя об отклонении заявки id=%s", application_id
        )

    await message.answer(APPLICATION_REJECTED_ADMIN_TEXT)
    text, keyboard = await _build_applications_queue_page(
        application_service, user_service, product_service, page
    )
    await message.answer(text, reply_markup=keyboard)


@router.message(ApplicationReviewStates.waiting_reject_reason)
async def handle_reject_reason_invalid(message: Message) -> None:
    """Отвечает на некорректный (нетекстовый) ввод во время ожидания причины отклонения."""
    await message.answer(REJECT_REASON_EMPTY_TEXT)


@router.callback_query(AdminApplicationsCallback.filter(F.action == "resend"))
async def handle_start_resend_request(
    callback: CallbackQuery, callback_data: AdminApplicationsCallback, state: FSMContext
) -> None:
    """Запускает ввод причины запроса повторной отправки скриншота заказа.

    Args:
        callback: Callback-запрос нажатия кнопки «🔄 Запросить повтор».
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        state: Контекст FSM текущего администратора.
    """
    await state.set_state(ApplicationReviewStates.waiting_resend_reason)
    await state.update_data(application_id=callback_data.application_id, page=callback_data.page)

    if isinstance(callback.message, Message):
        await callback.message.answer(ASK_RESEND_REASON_TEXT)
    await callback.answer()


@router.message(ApplicationReviewStates.waiting_resend_reason, F.text)
async def handle_resend_reason_input(
    message: Message,
    state: FSMContext,
    current_admin: Admin,
    application_service: ApplicationService,
    user_service: UserService,
    product_service: ProductService,
    fsm_storage: BaseStorage,
) -> None:
    """Запрашивает повторную отправку скриншота и возвращает FSM пользователя к его вводу.

    Args:
        message: Входящее сообщение с причиной запроса повтора.
        state: Контекст FSM текущего администратора.
        current_admin: Доменная сущность текущего администратора.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        user_service: Сервис пользователей, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
        fsm_storage: Хранилище FSM-состояний, внедряемое из workflow-данных диспетчера.
    """
    reason = (message.text or "").strip()
    if not reason:
        await message.answer(RESEND_REASON_EMPTY_TEXT)
        return

    data = await state.get_data()
    application_id: int = data["application_id"]
    page: int = data["page"]
    await state.clear()

    assert current_admin.id is not None
    try:
        application = await application_service.request_order_screenshot_resend(
            RequestOrderScreenshotResendDTO(
                application_id=application_id, admin_id=current_admin.id, reason=reason
            )
        )
    except (ApplicationNotFoundError, InvalidApplicationTransitionError):
        await message.answer(APPLICATION_NOT_FOUND_ADMIN_TEXT)
        return

    try:
        user = await user_service.get_by_id(application.user_id)
        assert message.bot is not None
        user_fsm_context = _build_user_fsm_context(fsm_storage, message.bot.id, user.telegram_id)
        await user_fsm_context.set_state(ApplicationFlowStates.waiting_order_screenshot)
        await user_fsm_context.update_data(application_id=application_id)
        await message.bot.send_message(
            chat_id=user.telegram_id,
            text=format_order_resend_requested_notification(reason),
        )
    except EntityNotFoundError:
        logger.warning("Пользователь для заявки id=%s не найден", application_id)
    except TelegramAPIError:
        logger.warning("Не удалось уведомить пользователя о запросе повтора id=%s", application_id)

    await message.answer(APPLICATION_RESEND_REQUESTED_ADMIN_TEXT)
    text, keyboard = await _build_applications_queue_page(
        application_service, user_service, product_service, page
    )
    await message.answer(text, reply_markup=keyboard)


@router.message(ApplicationReviewStates.waiting_resend_reason)
async def handle_resend_reason_invalid(message: Message) -> None:
    """Отвечает на некорректный (нетекстовый) ввод во время ожидания причины повтора."""
    await message.answer(RESEND_REASON_EMPTY_TEXT)
