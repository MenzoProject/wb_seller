"""FSM-состояния административных сценариев управления товарами.

`ProductFormStates` используется как для создания нового товара, так и
для его полного редактирования — сценарий определяется наличием ключа
`product_id` в данных FSM (отсутствует при создании, задан при
редактировании). По завершении мастера в обоих случаях собранные данные
передаются в `ProductService.create_product` либо `ProductService.update_product`.
"""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ProductFormStates(StatesGroup):
    """Состояния пошагового мастера создания или редактирования товара.

    Attributes:
        waiting_title: Ожидание названия товара.
        waiting_description: Ожидание описания товара.
        waiting_price: Ожидание цены товара.
        waiting_cashback_amount: Ожидание суммы кэшбэка.
        waiting_payout_days: Ожидание срока выплаты в днях.
        waiting_review_required: Ожидание ответа, требуется ли отзыв.
        waiting_receipt_required: Ожидание ответа, требуется ли чек.
        waiting_product_url: Ожидание ссылки на товар.
        waiting_instruction_text: Ожидание текста инструкции по заказу.
        waiting_available_slots: Ожидание количества доступных заявок.
        waiting_photo: Ожидание фотографии товара (или пропуска этого шага).
    """

    waiting_title = State()
    waiting_description = State()
    waiting_price = State()
    waiting_cashback_amount = State()
    waiting_payout_days = State()
    waiting_review_required = State()
    waiting_receipt_required = State()
    waiting_product_url = State()
    waiting_instruction_text = State()
    waiting_available_slots = State()
    waiting_photo = State()


class ProductSlotsChangeStates(StatesGroup):
    """Состояние быстрого изменения остатка доступных заявок товара.

    Attributes:
        waiting_new_slots: Ожидание нового количества доступных заявок.
    """

    waiting_new_slots = State()


class ApplicationReviewStates(StatesGroup):
    """Состояния FSM при рассмотрении заявки администратором.

    Attributes:
        waiting_reject_reason: Ожидание причины отклонения заявки.
        waiting_resend_reason: Ожидание причины запроса повторной отправки
            скриншота заказа.
    """

    waiting_reject_reason = State()
    waiting_resend_reason = State()
