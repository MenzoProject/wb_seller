"""Исключения доменного слоя, связанные с заявками и выплатами.

Выплата (`Payment`) неразрывно связана с заявкой (`Application`) — одна
заявка порождает не более одной выплаты, поэтому исключения, относящиеся
к выплатам, размещены в этом же модуле.
"""

from __future__ import annotations

from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.base import DomainError, EntityNotFoundError


class ApplicationNotFoundError(EntityNotFoundError):
    """Заявка с указанным идентификатором не найдена."""

    def __init__(self, application_id: int) -> None:
        """Инициализирует исключение отсутствия заявки.

        Args:
            application_id: Идентификатор запрашиваемой заявки.
        """
        super().__init__("Заявка", application_id)
        self.application_id = application_id


class InvalidApplicationTransitionError(DomainError):
    """Запрошен недопустимый переход статуса заявки.

    Attributes:
        current_status: Текущий статус заявки на момент попытки перехода.
        target_status: Статус, в который была совершена попытка перехода.
    """

    def __init__(
        self, current_status: ApplicationStatus, target_status: ApplicationStatus
    ) -> None:
        """Инициализирует исключение недопустимого перехода статуса.

        Args:
            current_status: Текущий статус заявки.
            target_status: Целевой статус, переход в который запрещён.
        """
        super().__init__(
            f"Недопустимый переход статуса заявки: "
            f"{current_status.value} -> {target_status.value}"
        )
        self.current_status = current_status
        self.target_status = target_status


class ApplicationRejectionReasonRequiredError(DomainError):
    """При отклонении заявки не была указана причина отклонения."""

    def __init__(self) -> None:
        """Инициализирует исключение отсутствия причины отклонения заявки."""
        super().__init__("Для отклонения заявки необходимо указать причину")


class ApplicationAlreadyHasPaymentError(DomainError):
    """Для заявки уже была создана выплата."""

    def __init__(self, application_id: int) -> None:
        """Инициализирует исключение повторного создания выплаты.

        Args:
            application_id: Идентификатор заявки, для которой уже существует выплата.
        """
        super().__init__(f"Для заявки id={application_id} уже создана выплата")
        self.application_id = application_id


class ApplicationAlreadyActiveError(DomainError):
    """У пользователя уже есть незавершённая заявка на этот же товар."""

    def __init__(self, user_id: int, product_id: int) -> None:
        """Инициализирует исключение дублирования активной заявки.

        Args:
            user_id: Внутренний идентификатор пользователя.
            product_id: Внутренний идентификатор товара.
        """
        super().__init__(
            f"У пользователя id={user_id} уже есть активная заявка на товар id={product_id}"
        )
        self.user_id = user_id
        self.product_id = product_id


class PaymentAlreadyPaidError(DomainError):
    """Выплата уже была отмечена как оплаченная."""

    def __init__(self, payment_id: int | None) -> None:
        """Инициализирует исключение повторной отметки выплаты как оплаченной.

        Args:
            payment_id: Идентификатор выплаты, уже находящейся в статусе PAID.
        """
        super().__init__(f"Выплата id={payment_id} уже отмечена как оплаченная")
        self.payment_id = payment_id
