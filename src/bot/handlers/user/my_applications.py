"""Обработчик раздела «📋 Мои заявки».

Показывает список заявок пользователя с текущими статусами. Для заявок,
ожидающих отзыва или ссылки на чек (если пользователь ранее прервал
ввод, перейдя в другой раздел меню), предлагает кнопки возобновления
соответствующего шага.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.services.application_service import ApplicationService
from src.application.services.product_service import ProductService
from src.bot.keyboards.user.applications import (
    ResumeApplicationCallback,
    get_resume_actions_keyboard,
)
from src.bot.keyboards.user.main_menu import MENU_MY_APPLICATIONS
from src.bot.states.user_states import ApplicationFlowStates
from src.bot.texts.user_texts import (
    ASK_RECEIPT_LINK_TEXT,
    ASK_REVIEW_SCREENSHOT_TEXT,
    INVALID_STATE_TRANSITION_TEXT,
    MY_APPLICATIONS_HEADER_TEXT,
    NO_APPLICATIONS_TEXT,
    format_application_status,
)
from src.domain.entities.user import User
from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.application_exceptions import ApplicationNotFoundError
from src.domain.exceptions.product_exceptions import ProductNotFoundError

router = Router(name="user_my_applications")

_APPLICATIONS_LIMIT = 20


@router.message(F.text == MENU_MY_APPLICATIONS)
async def handle_my_applications(
    message: Message,
    current_user: User,
    application_service: ApplicationService,
    product_service: ProductService,
) -> None:
    """Показывает список заявок пользователя с их текущими статусами.

    Args:
        message: Входящее сообщение с текстом кнопки «📋 Мои заявки».
        current_user: Доменная сущность текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
        product_service: Сервис товаров каталога, внедряемый `ServicesMiddleware`.
    """
    assert current_user.id is not None
    applications = await application_service.list_user_applications(
        current_user.id, limit=_APPLICATIONS_LIMIT, offset=0
    )

    if not applications:
        await message.answer(NO_APPLICATIONS_TEXT)
        return

    lines = [MY_APPLICATIONS_HEADER_TEXT, ""]
    resume_actions: list[tuple[str, ResumeApplicationCallback]] = []

    for application in applications:
        try:
            product = await product_service.get_product(application.product_id)
            product_title = product.title
        except ProductNotFoundError:
            product_title = f"товар #{application.product_id}"

        lines.append(
            f"№{application.id} · {product_title} · "
            f"{format_application_status(application.status)}"
        )

        assert application.id is not None
        if application.status == ApplicationStatus.WAIT_REVIEW:
            resume_actions.append(
                (
                    f"📸 №{application.id}: отправить отзыв",
                    ResumeApplicationCallback(action="review", application_id=application.id),
                )
            )
        elif application.status == ApplicationStatus.WAIT_RECEIPT_LINK:
            resume_actions.append(
                (
                    f"🧾 №{application.id}: отправить чек",
                    ResumeApplicationCallback(action="receipt", application_id=application.id),
                )
            )

    await message.answer(
        "\n".join(lines), reply_markup=get_resume_actions_keyboard(resume_actions)
    )


@router.callback_query(ResumeApplicationCallback.filter())
async def handle_resume_application_step(
    callback: CallbackQuery,
    callback_data: ResumeApplicationCallback,
    state: FSMContext,
    application_service: ApplicationService,
) -> None:
    """Возобновляет прерванный ранее шаг отправки отзыва или ссылки на чек.

    Args:
        callback: Callback-запрос нажатия кнопки возобновления шага.
        callback_data: Разобранные данные callback'а с действием и идентификатором заявки.
        state: Контекст FSM текущего пользователя.
        application_service: Сервис заявок, внедряемый `ServicesMiddleware`.
    """
    try:
        application = await application_service.get_application(callback_data.application_id)
    except ApplicationNotFoundError:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    if callback_data.action == "review" and application.status == ApplicationStatus.WAIT_REVIEW:
        await state.set_state(ApplicationFlowStates.waiting_review_screenshot)
        await state.update_data(application_id=application.id)
        if isinstance(callback.message, Message):
            await callback.message.answer(ASK_REVIEW_SCREENSHOT_TEXT)
    elif (
        callback_data.action == "receipt"
        and application.status == ApplicationStatus.WAIT_RECEIPT_LINK
    ):
        await state.set_state(ApplicationFlowStates.waiting_receipt_link)
        await state.update_data(application_id=application.id)
        if isinstance(callback.message, Message):
            await callback.message.answer(ASK_RECEIPT_LINK_TEXT)
    else:
        await callback.answer(INVALID_STATE_TRANSITION_TEXT, show_alert=True)
        return

    await callback.answer()
