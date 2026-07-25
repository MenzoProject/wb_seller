"""Обработчики жизненного цикла оформления заявки на стороне пользователя.

Покрывает полный путь заявки после её создания: артикул → скриншот
заказа → (после одобрения администратором) подтверждение получения →
выбор реквизитов → отзыв (если требуется) → ссылка на чек (если
требуется) → ожидание выплаты. Кнопка подтверждения получения
(`ConfirmReceiveCallback`) отправляется пользователю административным
обработчиком одобрения заказа, который будет реализован на следующем
этапе разработки (админ-бот, управление заявками).
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.dto.application_dto import (
    AssignRequisitesDTO,
    CancelApplicationDTO,
    ConfirmReceiveDTO,
    SubmitArticleDTO,
    SubmitOrderScreenshotDTO,
    SubmitReceiptLinkDTO,
    SubmitReviewScreenshotDTO,
)
from src.application.services.application_service import ApplicationService
from src.application.services.requisites_service import RequisitesService
from src.bot.keyboards.user.application_flow import (
    CancelApplicationCallback,
    ConfirmReceiveCallback,
    get_cancel_application_keyboard,
)
from src.bot.keyboards.user.main_menu import MENU_BUTTON_TEXTS, get_main_menu_keyboard
from src.bot.keyboards.user.requisites import (
    ApplicationRequisitesCallback,
    get_application_requisites_keyboard,
)
from src.bot.states.requisites_states import RequisitesStates
from src.bot.states.user_states import ApplicationFlowStates
from src.bot.texts.user_texts import (
    APPLICATION_CANCELLED_TEXT,
    ARTICLE_EMPTY_TEXT,
    ASK_FULL_NAME_TEXT,
    ASK_ORDER_SCREENSHOT_TEXT,
    ASK_RECEIPT_LINK_TEXT,
    ASK_REVIEW_SCREENSHOT_TEXT,
    INVALID_STATE_TRANSITION_TEXT,
    ORDER_SCREENSHOT_NOT_PHOTO_TEXT,
    ORDER_SUBMITTED_TEXT,
    RECEIPT_LINK_EMPTY_TEXT,
    RECEIVE_CONFIRMED_TEXT,
    REVIEW_SCREENSHOT_NOT_PHOTO_TEXT,
    format_wait_payment_text,
)
from src.bot.utils.admin_notify import notify_admins
from src.config.settings import AppSettings
from src.domain.entities.user import User
from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.application_exceptions import (
    ApplicationNotFoundError,
    InvalidApplicationTransitionError,
)
from src.domain.exceptions.requisites_exceptions import RequisitesNotFoundError

logger = logging.getLogger(__name__)

router = Router(name="user_application_flow")


@router.message(
    StateFilter(
        ApplicationFlowStates.waiting_article, ApplicationFlowStates.waiting_order_screenshot
    ),
    F.text.in_(MENU_BUTTON_TEXTS),
)
async def handle_menu_interrupts_early_flow(
    message: Message,
    state: FSMContext,
    current_user: User,
    application_service: ApplicationService,
) -> None:
    """Прерывает оформление заявки при переходе в другой раздел меню до её проверки.

    На этом этапе (ожидание артикула или скриншота заказа) заявка ещё не
    была рассмотрена администратором, поэтому переход в другой раздел
    меню трактуется как отказ от оформления: заявка отменяется, а
    зарезервированный слот товара освобождается.

    Args:
        message: Входящее сообщение с текстом кнопки главного меню.
        state: Контекст FSM текущего пользователя.
        current_user: Доменная сущность текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    assert current_user.id is not None

    data = await state.get_data()
    application_id = data.get("application_id")
    if application_id is not None:
        try:
            await application_service.cancel_by_user(
                CancelApplicationDTO(application_id=application_id, user_id=current_user.id)
            )
        except ApplicationNotFoundError:
            pass

    await state.clear()
    await message.answer(
        "Оформление заявки прервано. Нажмите на нужный раздел ещё раз.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(
    StateFilter(
        ApplicationFlowStates.waiting_review_screenshot,
        ApplicationFlowStates.waiting_receipt_link,
    ),
    F.text.in_(MENU_BUTTON_TEXTS),
)
async def handle_menu_interrupts_late_flow(message: Message, state: FSMContext) -> None:
    """Прерывает ввод отзыва или чека при переходе в другой раздел меню.

    В отличие от раннего этапа оформления, на этом шаге заказ уже одобрен
    администратором, поэтому заявка не отменяется — лишь сбрасывается
    текущий ввод. Продолжить отправку отзыва или чека можно из раздела
    «📋 Мои заявки».

    Args:
        message: Входящее сообщение с текстом кнопки главного меню.
        state: Контекст FSM текущего пользователя.
    """
    await state.clear()
    await message.answer(
        "Ввод прерван. Продолжить можно в любой момент из раздела «📋 Мои заявки».",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(ApplicationFlowStates.waiting_article, F.text)
async def handle_article_input(
    message: Message, state: FSMContext, application_service: ApplicationService
) -> None:
    """Фиксирует введённый пользователем артикул товара.

    Args:
        message: Входящее сообщение с текстом артикула.
        state: Контекст FSM текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    article = (message.text or "").strip()
    if not article:
        await message.answer(ARTICLE_EMPTY_TEXT)
        return

    data = await state.get_data()
    application_id: int = data["application_id"]

    application = await application_service.submit_article(
        SubmitArticleDTO(application_id=application_id, article=article)
    )

    await state.set_state(ApplicationFlowStates.waiting_order_screenshot)
    assert application.id is not None
    await message.answer(
        ASK_ORDER_SCREENSHOT_TEXT,
        reply_markup=get_cancel_application_keyboard(application.id),
    )


@router.message(ApplicationFlowStates.waiting_article)
async def handle_article_invalid_input(message: Message) -> None:
    """Отвечает на некорректный (нетекстовый) ввод во время ожидания артикула.

    Args:
        message: Входящее сообщение, не содержащее текста.
    """
    await message.answer(ARTICLE_EMPTY_TEXT)


@router.message(ApplicationFlowStates.waiting_order_screenshot, F.photo)
async def handle_order_screenshot(
    message: Message,
    state: FSMContext,
    current_user: User,
    application_service: ApplicationService,
    settings: AppSettings,
) -> None:
    """Фиксирует скриншот заказа и уведомляет администраторов о новой заявке на проверке.

    Args:
        message: Входящее сообщение с фотографией скриншота заказа.
        state: Контекст FSM текущего пользователя.
        current_user: Доменная сущность текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        settings: Настройки приложения, внедряемые из workflow-данных диспетчера.
    """
    data = await state.get_data()
    application_id: int = data["application_id"]

    assert message.photo is not None
    file_id = message.photo[-1].file_id

    application = await application_service.submit_order_screenshot(
        SubmitOrderScreenshotDTO(application_id=application_id, file_id=file_id)
    )

    await state.clear()
    await message.answer(ORDER_SUBMITTED_TEXT, reply_markup=get_main_menu_keyboard())

    assert message.bot is not None
    await notify_admins(
        bot=message.bot,
        admin_ids=settings.bot.admin_ids,
        text=(
            f"🆕 Новая заявка №{application.id} ожидает проверки.\n"
            f"Пользователь: {current_user.mention}\n"
            f"Артикул: {application.article}"
        ),
        photo_file_id=file_id,
    )


@router.message(ApplicationFlowStates.waiting_order_screenshot)
async def handle_order_screenshot_invalid(message: Message) -> None:
    """Отвечает на некорректный (нефото) ввод во время ожидания скриншота заказа.

    Args:
        message: Входящее сообщение, не содержащее фотографии.
    """
    await message.answer(ORDER_SCREENSHOT_NOT_PHOTO_TEXT)


@router.callback_query(CancelApplicationCallback.filter())
async def handle_cancel_application(
    callback: CallbackQuery,
    callback_data: CancelApplicationCallback,
    state: FSMContext,
    current_user: User,
    application_service: ApplicationService,
) -> None:
    """Отменяет заявку по нажатию кнопки «❌ Отмена» во время её оформления.

    Args:
        callback: Callback-запрос нажатия кнопки отмены.
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        state: Контекст FSM текущего пользователя.
        current_user: Доменная сущность текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    assert current_user.id is not None

    try:
        await application_service.cancel_by_user(
            CancelApplicationDTO(
                application_id=callback_data.application_id, user_id=current_user.id
            )
        )
    except ApplicationNotFoundError:
        await callback.answer("Заявка уже была обработана ранее.", show_alert=True)
        return

    await state.clear()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            APPLICATION_CANCELLED_TEXT, reply_markup=get_main_menu_keyboard()
        )
    await callback.answer()


@router.callback_query(ConfirmReceiveCallback.filter())
async def handle_confirm_receive(
    callback: CallbackQuery,
    callback_data: ConfirmReceiveCallback,
    current_user: User,
    application_service: ApplicationService,
    requisites_service: RequisitesService,
) -> None:
    """Фиксирует подтверждение получения товара и предлагает выбрать реквизиты для выплаты.

    Args:
        callback: Callback-запрос нажатия кнопки «✅ Я получил(а) товар».
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        current_user: Доменная сущность текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        requisites_service: Сервис реквизитов, внедряемый `ServicesMiddleware`.
    """
    try:
        application = await application_service.confirm_receive(
            ConfirmReceiveDTO(application_id=callback_data.application_id)
        )
    except (ApplicationNotFoundError, InvalidApplicationTransitionError):
        await callback.answer(INVALID_STATE_TRANSITION_TEXT, show_alert=True)
        return

    assert current_user.id is not None
    assert application.id is not None

    saved_requisites = await requisites_service.list_user_requisites(current_user.id)
    banks = await requisites_service.list_banks()
    banks_by_id = {bank.id: bank.name for bank in banks if bank.id is not None}

    keyboard = get_application_requisites_keyboard(application.id, saved_requisites, banks_by_id)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(RECEIVE_CONFIRMED_TEXT, reply_markup=keyboard)
    await callback.answer()


async def continue_flow_after_requisites_assigned(
    message: Message,
    application_id: int,
    application_service: ApplicationService,
    state: FSMContext,
) -> None:
    """Продолжает оформление заявки сразу после привязки к ней реквизитов.

    В зависимости от текущего статуса заявки запрашивает у пользователя
    отзыв, ссылку на чек, либо сообщает об ожидании выплаты, если
    дополнительные данные больше не требуются.

    Args:
        message: Сообщение, в ответ на которое отправляется следующий шаг
            (обычно исходное сообщение пользователя или сообщение бота,
            отредактированное callback-обработчиком).
        application_id: Внутренний идентификатор заявки.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        state: Контекст FSM текущего пользователя.
    """
    application = await application_service.get_application(application_id)

    if application.status == ApplicationStatus.WAIT_REVIEW:
        await state.set_state(ApplicationFlowStates.waiting_review_screenshot)
        await state.update_data(application_id=application_id)
        await message.answer(ASK_REVIEW_SCREENSHOT_TEXT)
    elif application.status == ApplicationStatus.WAIT_RECEIPT_LINK:
        await state.set_state(ApplicationFlowStates.waiting_receipt_link)
        await state.update_data(application_id=application_id)
        await message.answer(ASK_RECEIPT_LINK_TEXT)
    elif application.status == ApplicationStatus.WAIT_PAYMENT:
        await state.clear()
        await message.answer(format_wait_payment_text(application.payout_due_date))
    else:
        await state.clear()
        await message.answer(INVALID_STATE_TRANSITION_TEXT)


@router.callback_query(ApplicationRequisitesCallback.filter(F.action == "select"))
async def handle_select_existing_requisites(
    callback: CallbackQuery,
    callback_data: ApplicationRequisitesCallback,
    state: FSMContext,
    application_service: ApplicationService,
) -> None:
    """Привязывает выбранный существующий набор реквизитов к заявке и продолжает поток.

    Args:
        callback: Callback-запрос выбора набора реквизитов.
        callback_data: Разобранные данные callback'а с идентификаторами заявки и реквизитов.
        state: Контекст FSM текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    try:
        await application_service.assign_requisites(
            AssignRequisitesDTO(
                application_id=callback_data.application_id,
                requisites_id=callback_data.requisites_id,
            )
        )
    except RequisitesNotFoundError:
        await callback.answer(
            "Эти реквизиты больше недоступны. Выберите другие или добавьте новые.",
            show_alert=True,
        )
        return

    if isinstance(callback.message, Message):
        await continue_flow_after_requisites_assigned(
            callback.message, callback_data.application_id, application_service, state
        )
    await callback.answer()


@router.callback_query(ApplicationRequisitesCallback.filter(F.action == "add_new"))
async def handle_add_new_requisites_for_application(
    callback: CallbackQuery, callback_data: ApplicationRequisitesCallback, state: FSMContext
) -> None:
    """Запускает FSM добавления новых реквизитов в контексте конкретной заявки.

    Args:
        callback: Callback-запрос нажатия кнопки «➕ Указать новые реквизиты».
        callback_data: Разобранные данные callback'а с идентификатором заявки.
        state: Контекст FSM текущего пользователя.
    """
    await state.set_state(RequisitesStates.waiting_full_name)
    await state.update_data(application_id=callback_data.application_id)

    if isinstance(callback.message, Message):
        await callback.message.answer(ASK_FULL_NAME_TEXT)
    await callback.answer()


@router.message(ApplicationFlowStates.waiting_review_screenshot, F.photo)
async def handle_review_screenshot(
    message: Message, state: FSMContext, application_service: ApplicationService
) -> None:
    """Фиксирует скриншот отзыва и продолжает оформление заявки.

    Args:
        message: Входящее сообщение с фотографией скриншота отзыва.
        state: Контекст FSM текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    data = await state.get_data()
    application_id: int = data["application_id"]

    assert message.photo is not None
    file_id = message.photo[-1].file_id

    await application_service.submit_review_screenshot(
        SubmitReviewScreenshotDTO(application_id=application_id, file_id=file_id)
    )
    await continue_flow_after_requisites_assigned(
        message, application_id, application_service, state
    )


@router.message(ApplicationFlowStates.waiting_review_screenshot)
async def handle_review_screenshot_invalid(message: Message) -> None:
    """Отвечает на некорректный (нефото) ввод во время ожидания скриншота отзыва.

    Args:
        message: Входящее сообщение, не содержащее фотографии.
    """
    await message.answer(REVIEW_SCREENSHOT_NOT_PHOTO_TEXT)


@router.message(ApplicationFlowStates.waiting_receipt_link, F.text)
async def handle_receipt_link(
    message: Message, state: FSMContext, application_service: ApplicationService
) -> None:
    """Фиксирует ссылку на чек и завершает сбор данных, переводя заявку в ожидание выплаты.

    Args:
        message: Входящее сообщение со ссылкой на чек.
        state: Контекст FSM текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    receipt_link = (message.text or "").strip()
    if not receipt_link:
        await message.answer(RECEIPT_LINK_EMPTY_TEXT)
        return

    data = await state.get_data()
    application_id: int = data["application_id"]

    await application_service.submit_receipt_link(
        SubmitReceiptLinkDTO(application_id=application_id, receipt_link=receipt_link)
    )
    await continue_flow_after_requisites_assigned(
        message, application_id, application_service, state
    )


@router.message(ApplicationFlowStates.waiting_receipt_link)
async def handle_receipt_link_invalid(message: Message) -> None:
    """Отвечает на некорректный (нетекстовый) ввод во время ожидания ссылки на чек.

    Args:
        message: Входящее сообщение, не содержащее текста.
    """
    await message.answer(RECEIPT_LINK_EMPTY_TEXT)
