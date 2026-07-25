"""Обработчики раздела «💳 Реквизиты».

FSM добавления реквизитов используется в двух сценариях: самостоятельное
управление реквизитами через главное меню и добавление новых реквизитов
прямо в процессе оформления заявки (см. `application_flow.py`). Сценарий
определяется наличием ключа `application_id` в данных FSM — если он
присутствует, после сохранения реквизитов оформление заявки продолжается
автоматически через `continue_flow_after_requisites_assigned`.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.dto.application_dto import AssignRequisitesDTO
from src.application.dto.requisites_dto import CreateRequisitesDTO
from src.application.services.application_service import ApplicationService
from src.application.services.requisites_service import RequisitesService
from src.bot.handlers.user.application_flow import continue_flow_after_requisites_assigned
from src.bot.keyboards.user.main_menu import (
    MENU_BUTTON_TEXTS,
    MENU_REQUISITES,
    get_main_menu_keyboard,
)
from src.bot.keyboards.user.requisites import (
    BankSelectCallback,
    RequisitesCallback,
    get_bank_selection_keyboard,
    get_requisites_management_keyboard,
)
from src.bot.states.requisites_states import RequisitesStates
from src.bot.texts.user_texts import (
    ASK_BANK_TEXT,
    ASK_FULL_NAME_TEXT,
    ASK_PHONE_TEXT,
    FULL_NAME_TOO_SHORT_TEXT,
    NO_BANKS_AVAILABLE_TEXT,
    NO_REQUISITES_TEXT,
    PHONE_INVALID_TEXT,
    REQUISITES_DELETED_TEXT,
    REQUISITES_HEADER_TEXT,
    REQUISITES_SAVED_TEXT,
    REQUISITES_SET_DEFAULT_TEXT,
)
from src.domain.entities.user import User
from src.domain.exceptions.requisites_exceptions import (
    InvalidRequisitesDataError,
    RequisitesNotFoundError,
)

router = Router(name="user_requisites")

_MIN_FULL_NAME_LENGTH = 3


async def _render_requisites_screen(
    message: Message, user_id: int, requisites_service: RequisitesService
) -> None:
    """Отправляет сообщение со списком реквизитов пользователя и клавиатурой управления.

    Args:
        message: Сообщение, в ответ на которое отправляется экран реквизитов.
        user_id: Внутренний идентификатор пользователя.
        requisites_service: Сервис реквизитов, внедряемый `ServicesMiddleware`.
    """
    requisites_list = await requisites_service.list_user_requisites(user_id)
    banks = await requisites_service.list_banks()
    banks_by_id = {bank.id: bank.name for bank in banks if bank.id is not None}

    if not requisites_list:
        text = f"{REQUISITES_HEADER_TEXT}\n\n{NO_REQUISITES_TEXT}"
    else:
        text = REQUISITES_HEADER_TEXT

    await message.answer(
        text, reply_markup=get_requisites_management_keyboard(requisites_list, banks_by_id)
    )


@router.message(F.text == MENU_REQUISITES)
async def handle_requisites_menu(
    message: Message, current_user: User, requisites_service: RequisitesService
) -> None:
    """Показывает раздел управления реквизитами по нажатию кнопки главного меню.

    Args:
        message: Входящее сообщение с текстом кнопки «💳 Реквизиты».
        current_user: Доменная сущность текущего пользователя.
        requisites_service: Сервис реквизитов, внедряемый `ServicesMiddleware`.
    """
    assert current_user.id is not None
    await _render_requisites_screen(message, current_user.id, requisites_service)


@router.callback_query(RequisitesCallback.filter(F.action == "add"))
async def handle_start_add_requisites(callback: CallbackQuery, state: FSMContext) -> None:
    """Запускает FSM добавления реквизитов из раздела самостоятельного управления.

    Args:
        callback: Callback-запрос нажатия кнопки «➕ Добавить реквизиты».
        state: Контекст FSM текущего пользователя.
    """
    await state.set_state(RequisitesStates.waiting_full_name)
    await state.update_data(application_id=None)

    if isinstance(callback.message, Message):
        await callback.message.answer(ASK_FULL_NAME_TEXT)
    await callback.answer()


@router.callback_query(RequisitesCallback.filter(F.action == "set_default"))
async def handle_set_default_requisites(
    callback: CallbackQuery,
    callback_data: RequisitesCallback,
    current_user: User,
    requisites_service: RequisitesService,
) -> None:
    """Назначает выбранный набор реквизитов используемым по умолчанию.

    Args:
        callback: Callback-запрос нажатия на строку набора реквизитов.
        callback_data: Разобранные данные callback'а с идентификатором реквизитов.
        current_user: Доменная сущность текущего пользователя.
        requisites_service: Сервис реквизитов, внедряемый `ServicesMiddleware`.
    """
    assert current_user.id is not None
    try:
        await requisites_service.set_default(callback_data.requisites_id, current_user.id)
    except RequisitesNotFoundError:
        await callback.answer("Реквизиты не найдены.", show_alert=True)
        return

    await callback.answer(REQUISITES_SET_DEFAULT_TEXT)
    if isinstance(callback.message, Message):
        await _render_requisites_screen(callback.message, current_user.id, requisites_service)


@router.callback_query(RequisitesCallback.filter(F.action == "delete"))
async def handle_delete_requisites(
    callback: CallbackQuery,
    callback_data: RequisitesCallback,
    current_user: User,
    requisites_service: RequisitesService,
) -> None:
    """Удаляет выбранный набор реквизитов пользователя.

    Args:
        callback: Callback-запрос нажатия кнопки «🗑».
        callback_data: Разобранные данные callback'а с идентификатором реквизитов.
        current_user: Доменная сущность текущего пользователя.
        requisites_service: Сервис реквизитов, внедряемый `ServicesMiddleware`.
    """
    assert current_user.id is not None
    try:
        await requisites_service.delete_requisites(callback_data.requisites_id, current_user.id)
    except RequisitesNotFoundError:
        await callback.answer("Реквизиты не найдены.", show_alert=True)
        return

    await callback.answer(REQUISITES_DELETED_TEXT)
    if isinstance(callback.message, Message):
        await _render_requisites_screen(callback.message, current_user.id, requisites_service)


@router.message(
    StateFilter(
        RequisitesStates.waiting_full_name,
        RequisitesStates.waiting_phone,
        RequisitesStates.waiting_bank,
    ),
    F.text.in_(MENU_BUTTON_TEXTS),
)
async def handle_menu_interrupts_requisites_flow(message: Message, state: FSMContext) -> None:
    """Прерывает добавление реквизитов при переходе пользователя в другой раздел меню.

    Args:
        message: Входящее сообщение с текстом кнопки главного меню.
        state: Контекст FSM текущего пользователя.
    """
    await state.clear()
    await message.answer(
        "Добавление реквизитов прервано. Нажмите на нужный раздел ещё раз.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(RequisitesStates.waiting_full_name, F.text)
async def handle_full_name_input(message: Message, state: FSMContext) -> None:
    """Фиксирует введённое пользователем ФИО получателя выплаты.

    Args:
        message: Входящее сообщение с текстом ФИО.
        state: Контекст FSM текущего пользователя.
    """
    full_name = (message.text or "").strip()
    if len(full_name) < _MIN_FULL_NAME_LENGTH:
        await message.answer(FULL_NAME_TOO_SHORT_TEXT)
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RequisitesStates.waiting_phone)
    await message.answer(ASK_PHONE_TEXT)


@router.message(RequisitesStates.waiting_full_name)
async def handle_full_name_invalid(message: Message) -> None:
    """Отвечает на некорректный (нетекстовый) ввод во время ожидания ФИО.

    Args:
        message: Входящее сообщение, не содержащее текста.
    """
    await message.answer(FULL_NAME_TOO_SHORT_TEXT)


@router.message(RequisitesStates.waiting_phone, F.text)
async def handle_phone_input(
    message: Message, state: FSMContext, requisites_service: RequisitesService
) -> None:
    """Фиксирует введённый пользователем номер телефона и показывает выбор банка.

    Args:
        message: Входящее сообщение с текстом номера телефона.
        state: Контекст FSM текущего пользователя.
        requisites_service: Сервис реквизитов, внедряемый `ServicesMiddleware`.
    """
    phone = (message.text or "").strip()
    digits_only = "".join(character for character in phone if character.isdigit())
    if len(digits_only) < 10:
        await message.answer(PHONE_INVALID_TEXT)
        return

    banks = await requisites_service.list_banks()
    if not banks:
        await message.answer(NO_BANKS_AVAILABLE_TEXT)
        await state.clear()
        return

    await state.update_data(phone=phone)
    await state.set_state(RequisitesStates.waiting_bank)
    await message.answer(ASK_BANK_TEXT, reply_markup=get_bank_selection_keyboard(banks))


@router.message(RequisitesStates.waiting_phone)
async def handle_phone_invalid(message: Message) -> None:
    """Отвечает на некорректный (нетекстовый) ввод во время ожидания номера телефона.

    Args:
        message: Входящее сообщение, не содержащее текста.
    """
    await message.answer(PHONE_INVALID_TEXT)


@router.callback_query(RequisitesStates.waiting_bank, BankSelectCallback.filter())
async def handle_bank_selected(
    callback: CallbackQuery,
    callback_data: BankSelectCallback,
    state: FSMContext,
    current_user: User,
    requisites_service: RequisitesService,
    application_service: ApplicationService,
) -> None:
    """Завершает добавление реквизитов после выбора банка и продолжает соответствующий сценарий.

    Args:
        callback: Callback-запрос выбора банка.
        callback_data: Разобранные данные callback'а с идентификатором банка.
        state: Контекст FSM текущего пользователя.
        current_user: Доменная сущность текущего пользователя.
        requisites_service: Сервис реквизитов, внедряемый `ServicesMiddleware`.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    assert current_user.id is not None
    data = await state.get_data()
    full_name: str = data["full_name"]
    phone: str = data["phone"]
    application_id: int | None = data.get("application_id")

    try:
        created_requisites = await requisites_service.create_requisites(
            CreateRequisitesDTO(
                user_id=current_user.id,
                full_name=full_name,
                phone=phone,
                bank_id=callback_data.bank_id,
            )
        )
    except InvalidRequisitesDataError:
        await callback.answer(
            "Не удалось сохранить реквизиты — проверьте корректность данных.", show_alert=True
        )
        await state.clear()
        return

    if application_id is not None and isinstance(callback.message, Message):
        # Если у пользователя уже были другие реквизиты, только что созданный
        # набор не становится автоматически выбранным по умолчанию — привязываем
        # его к текущей заявке явно, вне зависимости от is_default.
        if created_requisites.id is not None:
            await application_service.assign_requisites(
                AssignRequisitesDTO(
                    application_id=application_id, requisites_id=created_requisites.id
                )
            )
        await callback.message.answer(REQUISITES_SAVED_TEXT)
        await continue_flow_after_requisites_assigned(
            callback.message, application_id, application_service, state
        )
    else:
        await state.clear()
        if isinstance(callback.message, Message):
            await callback.message.answer(REQUISITES_SAVED_TEXT)
            await _render_requisites_screen(callback.message, current_user.id, requisites_service)

    await callback.answer()
