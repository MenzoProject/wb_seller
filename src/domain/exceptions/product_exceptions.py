"""Исключения доменного слоя, связанные с товарами каталога."""

from __future__ import annotations

from src.domain.exceptions.base import DomainError, EntityNotFoundError


class ProductNotFoundError(EntityNotFoundError):
    """Товар с указанным идентификатором не найден."""

    def __init__(self, product_id: int) -> None:
        """Инициализирует исключение отсутствия товара.

        Args:
            product_id: Идентификатор запрашиваемого товара.
        """
        super().__init__("Товар", product_id)
        self.product_id = product_id


class ProductOutOfStockError(DomainError):
    """У товара закончились доступные слоты для оформления заявок."""

    def __init__(self, product_id: int | None) -> None:
        """Инициализирует исключение отсутствия доступных слотов.

        Args:
            product_id: Идентификатор товара, у которого закончились слоты.
        """
        super().__init__(f"У товара id={product_id} закончились доступные слоты для заявок")
        self.product_id = product_id


class ProductUnavailableError(DomainError):
    """Товар скрыт или удалён и недоступен для оформления заявки."""

    def __init__(self, product_id: int | None) -> None:
        """Инициализирует исключение недоступности товара.

        Args:
            product_id: Идентификатор недоступного товара.
        """
        super().__init__(f"Товар id={product_id} скрыт или удалён и недоступен для заказа")
        self.product_id = product_id


class ProductValidationError(DomainError):
    """Данные товара не прошли валидацию при создании или редактировании."""

    def __init__(self, message: str) -> None:
        """Инициализирует исключение валидации данных товара.

        Args:
            message: Описание конкретной ошибки валидации.
        """
        super().__init__(message)
