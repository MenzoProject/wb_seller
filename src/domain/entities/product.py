"""Доменная сущность товара каталога."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from src.domain.exceptions.product_exceptions import (
    ProductOutOfStockError,
    ProductUnavailableError,
    ProductValidationError,
)


@dataclass(slots=True)
class Product:
    """Товар, доступный для оформления заявки на выкуп с кэшбэком.

    Attributes:
        id: Внутренний идентификатор товара. `None` для ещё не сохранённой
            в базе данных сущности.
        title: Название товара.
        description: Описание товара для отображения в каталоге.
        price: Цена, которую реселлер платит при заказе товара.
        cashback_amount: Сумма кэшбэка, выплачиваемая после выполнения условий.
        payout_days: Количество дней от наступления условия выплаты до даты выплаты.
        review_required: Признак того, что для получения кэшбэка требуется отзыв.
        receipt_required: Признак того, что для получения кэшбэка требуется чек об оплате.
        product_url: Ссылка на карточку товара на маркетплейсе.
        instruction_text: Текстовая инструкция по оформлению заказа для этого товара.
        available_slots: Количество доступных для оформления заявок по товару.
        is_hidden: Признак скрытия товара из каталога (временно недоступен).
        is_deleted: Признак мягкого удаления товара (soft delete).
        photo_file_ids: Список file_id фотографий товара в Telegram, в порядке отображения.
        created_at: Дата и время создания товара.
        updated_at: Дата и время последнего обновления товара.
    """

    id: int | None
    title: str
    description: str
    price: Decimal
    cashback_amount: Decimal
    payout_days: int
    review_required: bool
    receipt_required: bool
    product_url: str
    instruction_text: str
    available_slots: int = 0
    is_hidden: bool = False
    is_deleted: bool = False
    photo_file_ids: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Проверяет базовые инварианты товара сразу после создания сущности.

        Raises:
            ProductValidationError: Если название товара пустое, цена или
                сумма кэшбэка отрицательны, либо срок выплаты некорректен.
        """
        if not self.title.strip():
            raise ProductValidationError("Название товара не может быть пустым")
        if self.price < 0:
            raise ProductValidationError("Цена товара не может быть отрицательной")
        if self.cashback_amount < 0:
            raise ProductValidationError("Сумма кэшбэка не может быть отрицательной")
        if self.payout_days <= 0:
            raise ProductValidationError("Срок выплаты должен быть положительным числом дней")
        if self.available_slots < 0:
            raise ProductValidationError("Количество доступных заявок не может быть отрицательным")

    @property
    def is_available_for_order(self) -> bool:
        """Признак того, что товар доступен для оформления новой заявки.

        Returns:
            True, если товар не скрыт, не удалён и имеет свободные слоты заявок.
        """
        return not self.is_hidden and not self.is_deleted and self.available_slots > 0

    def ensure_available_for_order(self) -> None:
        """Проверяет доступность товара для оформления заявки, выбрасывая исключение при отказе.

        Raises:
            ProductUnavailableError: Если товар скрыт или удалён из каталога.
            ProductOutOfStockError: Если у товара закончились доступные слоты заявок.
        """
        if self.is_hidden or self.is_deleted:
            raise ProductUnavailableError(self.id)
        if self.available_slots <= 0:
            raise ProductOutOfStockError(self.id)

    def reserve_slot(self) -> None:
        """Резервирует один слот товара при создании новой заявки.

        Raises:
            ProductUnavailableError: Если товар скрыт или удалён.
            ProductOutOfStockError: Если свободные слоты отсутствуют.
        """
        self.ensure_available_for_order()
        self.available_slots -= 1

    def release_slot(self) -> None:
        """Возвращает один слот товара, например при отклонении заявки."""
        self.available_slots += 1

    def hide(self) -> None:
        """Скрывает товар из каталога, не удаляя его безвозвратно."""
        self.is_hidden = True

    def unhide(self) -> None:
        """Возвращает ранее скрытый товар в каталог."""
        self.is_hidden = False

    def mark_deleted(self) -> None:
        """Помечает товар как удалённый (мягкое удаление)."""
        self.is_deleted = True
        self.is_hidden = True
