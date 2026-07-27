"""Обработчики раздела «🏦 Банки» панели администратора.

Позволяет администратору просматривать полный справочник банков,
добавлять новые банки и включать/отключать существующие — без этого
раздела пользователи не могут сохранить платёжные реквизиты, если
справочник банков окажется пуст (см. `RequisitesService.list_banks`,
используемый в пользовательском сценарии добавления реквизитов).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from src.application.services.requisites_service import RequisitesService
from src.bot.keyboards.admin.banks import (
    AdminBanksCallback,
    get_admin_banks_list_keyboard,
    get_admin_settings_keyboard,
)
from src.bot.keyboards.admin.main_menu import ADMIN_MENU_SETTINGS
from src.bot.states.admin_states import BankFormStates
from src.bot.texts.admin_texts import (
    ADMIN_BANKS_EMPTY_TEXT,
    ADMIN_BANKS_HEADER_TEXT,
    ADMIN_SETTINGS_HEADER_TEXT,
    ASK_BANK_NAME_TEXT,
    BANK_ACTIVATED_TEXT,
    BANK_CREATED_TEXT,
    BANK_DEACTIVATED_TEXT,
    BANK_NAME_ALREADY_EXISTS_TEXT,
    BANK_NAME_TOO_SHORT_TEXT,
    BANK_NOT_FOUND_TEXT,
)
from src.domain.exceptions.requisites_exceptions import (
    BankNameAlreadyExistsError,
    BankNotFoundError,
)

router = Router(name="admin_banks")

_MIN_BANK_NAME_LENGTH = 2


async def _banks_list_text_and_keyboard(
    requisites_service: RequisitesService,
) -> tuple[str, InlineKeyboardMarkup]:
    """Формирует текст и клавиатуру экрана справочника банков.

    Args:
        requisites_service: Сервис реквизитов и банков, внедряемый `ServicesMiddleware`.

    Returns:
        Пара (текст сообщения, инлайн-клавиатура списка банков).
    """
    banks = await requisites_service.list_all_banks()
    text = ADMIN_BANKS_HEADER_TEXT
    if not banks:
        text = f"{ADMIN_BANKS_HEADER_TEXT}\n\n{ADMIN_BANKS_EMPTY_TEXT}"
    return text, get_admin_banks_list_keyboard(banks)


async def _render_banks_list(message: Message, requisites_service: RequisitesService) -> None:
    """Отправляет новое сообщение со списком банков и клавиатурой управления.

    Args:
        message: Сообщение, в ответ на которое отправляется экран списка банков.
        requisites_service: Сервис реквизитов и банков, внедряемый `ServicesMiddleware`.
    """
    text, keyboard = await _banks_list_text_and_keyboard(requisites_service)
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == ADMIN_MENU_SETTINGS)
async def handle_admin_settings_menu(message: Message) -> None:
    """Открывает раздел «⚙ Настройки» панели администратора.

    Args:
        message: Входящее сообщение с текстом кнопки «⚙ Настройки».
    """
    await message.answer(ADMIN_SETTINGS_HEADER_TEXT, reply_markup=get_admin_settings_keyboard())


@router.callback_query(AdminBanksCallback.filter(F.action == "list"))
async def handle_banks_list(
    callback: CallbackQuery, requisites_service: RequisitesService
) -> None:
    """Показывает справочник банков по нажатию кнопки «🏦 Банки».

    Args:
        callback: Callback-запрос нажатия кнопки «🏦 Банки».
        requisites_service: Сервис реквизитов и банков, внедряемый `ServicesMiddleware`.
    """
    if isinstance(callback.message, Message):
        text, keyboard = await _banks_list_text_and_keyboard(requisites_service)
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(AdminBanksCallback.filter(F.action == "toggle"))
async def handle_bank_toggle(
    callback: CallbackQuery,
    callback_data: AdminBanksCallback,
    requisites_service: RequisitesService,
) -> None:
    """Переключает доступность банка для выбора пользователями.

    Args:
        callback: Callback-запрос нажатия кнопки конкретного банка.
        callback_data: Разобранные данные callback'а с идентификатором банка.
        requisites_service: Сервис реквизитов и банков, внедряемый `ServicesMiddleware`.
    """
    try:
        all_banks = await requisites_service.list_all_banks()
        current = next((item for item in all_banks if item.id == callback_data.bank_id), None)
        if current is None:
            raise BankNotFoundError(callback_data.bank_id)

        updated_bank = await requisites_service.set_bank_active(
            callback_data.bank_id, not current.is_active
        )
    except BankNotFoundError:
        await callback.answer(BANK_NOT_FOUND_TEXT, show_alert=True)
        if isinstance(callback.message, Message):
            text, keyboard = await _banks_list_text_and_keyboard(requisites_service)
            await callback.message.edit_text(text, reply_markup=keyboard)
        return

    await callback.answer(BANK_ACTIVATED_TEXT if updated_bank.is_active else BANK_DEACTIVATED_TEXT)
    if isinstance(callback.message, Message):
        text, keyboard = await _banks_list_text_and_keyboard(requisites_service)
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(AdminBanksCallback.filter(F.action == "create"))
async def handle_bank_create_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Запускает FSM добавления нового банка в справочник.

    Args:
        callback: Callback-запрос нажатия кнопки «➕ Добавить банк».
        state: Контекст FSM текущего администратора.
    """
    await state.set_state(BankFormStates.waiting_name)
    if isinstance(callback.message, Message):
        await callback.message.answer(ASK_BANK_NAME_TEXT)
    await callback.answer()


@router.message(BankFormStates.waiting_name, F.text)
async def handle_bank_name_input(
    message: Message, state: FSMContext, requisites_service: RequisitesService
) -> None:
    """Фиксирует введённое администратором название нового банка.

    Args:
        message: Входящее сообщение с названием банка.
        state: Контекст FSM текущего администратора.
        requisites_service: Сервис реквизитов и банков, внедряемый `ServicesMiddleware`.
    """
    name = (message.text or "").strip()
    if len(name) < _MIN_BANK_NAME_LENGTH:
        await message.answer(BANK_NAME_TOO_SHORT_TEXT)
        return

    try:
        await requisites_service.create_bank(name)
    except BankNameAlreadyExistsError:
        await message.answer(BANK_NAME_ALREADY_EXISTS_TEXT)
        return

    await state.clear()
    await message.answer(BANK_CREATED_TEXT)
    await _render_banks_list(message, requisites_service)


@router.message(BankFormStates.waiting_name)
async def handle_bank_name_invalid(message: Message) -> None:
    """Отвечает на некорректный (нетекстовый) ввод во время ожидания названия банка.

    Args:
        message: Входящее сообщение, не содержащее текста.
    """
    await message.answer(BANK_NAME_TOO_SHORT_TEXT)
