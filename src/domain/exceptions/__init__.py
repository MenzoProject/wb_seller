"""Исключения доменного слоя."""

from src.domain.exceptions.application_exceptions import (
    ApplicationAlreadyActiveError,
    ApplicationAlreadyHasPaymentError,
    ApplicationNotFoundError,
    ApplicationRejectionReasonRequiredError,
    InvalidApplicationTransitionError,
    PaymentAlreadyPaidError,
)
from src.domain.exceptions.base import DomainError, EntityNotFoundError
from src.domain.exceptions.product_exceptions import (
    ProductNotFoundError,
    ProductOutOfStockError,
    ProductUnavailableError,
    ProductValidationError,
)
from src.domain.exceptions.requisites_exceptions import (
    BankInactiveError,
    BankNotFoundError,
    InvalidRequisitesDataError,
    RequisitesNotFoundError,
)

__all__ = [
    "DomainError",
    "EntityNotFoundError",
    "ApplicationAlreadyActiveError",
    "ApplicationAlreadyHasPaymentError",
    "ApplicationNotFoundError",
    "ApplicationRejectionReasonRequiredError",
    "InvalidApplicationTransitionError",
    "PaymentAlreadyPaidError",
    "ProductNotFoundError",
    "ProductOutOfStockError",
    "ProductUnavailableError",
    "ProductValidationError",
    "BankInactiveError",
    "BankNotFoundError",
    "InvalidRequisitesDataError",
    "RequisitesNotFoundError",
]
