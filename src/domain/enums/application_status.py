"""Статусы заявки реселлера на выкуп товара."""

from __future__ import annotations

import enum


class ApplicationStatus(str, enum.Enum):
    """Статусы жизненного цикла заявки.

    Заявка проходит по цепочке статусов от создания до выплаты кэшбэка.
    На любом этапе проверки администратор может отклонить заявку
    (перевод в REJECTED) либо запросить повторную отправку данных
    (возврат в один из WAIT_-статусов).
    """

    NEW = "NEW"
    WAIT_ORDER_SCREEN = "WAIT_ORDER_SCREEN"
    ORDER_ON_REVIEW = "ORDER_ON_REVIEW"
    ORDER_APPROVED = "ORDER_APPROVED"
    WAIT_RECEIVE = "WAIT_RECEIVE"
    WAIT_REVIEW = "WAIT_REVIEW"
    WAIT_RECEIPT_LINK = "WAIT_RECEIPT_LINK"
    WAIT_PAYMENT = "WAIT_PAYMENT"
    PAID = "PAID"
    REJECTED = "REJECTED"

    @property
    def is_terminal(self) -> bool:
        """Признак того, что статус является финальным для заявки.

        Returns:
            True, если заявка находится в статусе PAID или REJECTED и
            дальнейшие переходы по бизнес-процессу невозможны.
        """
        return self in (ApplicationStatus.PAID, ApplicationStatus.REJECTED)

    @property
    def is_waiting_user_action(self) -> bool:
        """Признак того, что статус ожидает действия от пользователя.

        Returns:
            True, если для перехода к следующему статусу требуется
            какое-либо действие пользователя (отправка скрина, ссылки и т.д.).
        """
        return self in (
            ApplicationStatus.WAIT_ORDER_SCREEN,
            ApplicationStatus.WAIT_RECEIVE,
            ApplicationStatus.WAIT_REVIEW,
            ApplicationStatus.WAIT_RECEIPT_LINK,
        )

    @property
    def is_waiting_admin_action(self) -> bool:
        """Признак того, что статус ожидает решения администратора.

        Returns:
            True, если заявка находится на проверке у администратора
            либо ожидает наступления даты выплаты.
        """
        return self in (
            ApplicationStatus.ORDER_ON_REVIEW,
            ApplicationStatus.WAIT_PAYMENT,
        )
