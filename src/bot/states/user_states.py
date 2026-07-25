"""FSM-состояния процесса оформления заявки пользователем.

Не каждый шаг жизненного цикла заявки требует состояния FSM — только те,
что ожидают свободного текстового или медиа-ввода от пользователя.
Переход "подтверждаю получение" и другие шаги, выполняемые нажатием
инлайн-кнопки, обрабатываются как обычные stateless callback-обработчики.
"""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ApplicationFlowStates(StatesGroup):
    """Состояния FSM в процессе оформления и сопровождения заявки.

    Attributes:
        waiting_article: Ожидание артикула товара после выбора товара в каталоге.
        waiting_order_screenshot: Ожидание скриншота подтверждения заказа.
        waiting_review_screenshot: Ожидание скриншота оставленного отзыва.
        waiting_receipt_link: Ожидание ссылки на чек об оплате.
    """

    waiting_article = State()
    waiting_order_screenshot = State()
    waiting_review_screenshot = State()
    waiting_receipt_link = State()
