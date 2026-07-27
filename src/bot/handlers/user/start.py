"""Обработчик команды /start.

Приветствует пользователя и показывает главное меню. Если на момент
вызова команды пользователь находился в процессе оформления заявки,
незавершённая заявка автоматически отменяется с освобождением
зарезервированного слота товара.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.application.dto.application_dto import CancelApplicationDTO
from src.application.services.application_service import ApplicationService
from src.bot.keyboards.user.main_menu import get_main_menu_keyboard
from src.bot.texts.user_texts import WELCOME_TEXT
from src.domain.entities.user import User
from src.domain.exceptions.application_exceptions import ApplicationNotFoundError

logger = logging.getLogger(__name__)

router = Router(name="user_start")


@router.message(CommandStart())
async def handle_start(
    message: Message,
    current_user: User,
    state: FSMContext,
    application_service: ApplicationService,
) -> None:
    """Обрабатывает команду /start: приветствует пользователя и показывает главное меню.

    Args:
        message: Входящее сообщение с командой /start.
        current_user: Доменная сущность текущего пользователя, внедрённая
            `UserRegistrationMiddleware`.
        state: Контекст FSM текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    data = await state.get_data()
    application_id = data.get("application_id")
    if application_id is not None:
        assert current_user.id is not None
        try:
            await application_service.cancel_by_user(
                CancelApplicationDTO(application_id=application_id, user_id=current_user.id)
            )
        except ApplicationNotFoundError:
            logger.info(
                "Заявка id=%s уже была обработана к моменту вызова /start пользователем id=%s",
                application_id,
                current_user.id,
            )
    await state.clear()

    await message.answer(
        WELCOME_TEXT.format(full_name=current_user.full_name),
        reply_markup=get_main_menu_keyboard(),
    )
