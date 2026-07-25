"""DTO для операций создания и редактирования товаров каталога."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreateDTO(BaseModel):
    """Данные, необходимые для создания нового товара в каталоге.

    Attributes:
        title: Название товара.
        description: Описание товара для отображения в каталоге.
        price: Цена, которую реселлер платит при заказе товара.
        cashback_amount: Сумма кэшбэка, выплачиваемая после выполнения условий.
        payout_days: Количество дней от наступления условия выплаты до даты выплаты.
        review_required: Требуется ли для получения кэшбэка отзыв.
        receipt_required: Требуется ли для получения кэшбэка ссылка на чек.
        product_url: Ссылка на карточку товара на маркетплейсе.
        instruction_text: Текстовая инструкция по оформлению заказа.
        available_slots: Количество доступных для оформления заявок по товару.
        photo_file_ids: Список file_id фотографий товара в Telegram.
        admin_id: Внутренний идентификатор администратора, создающего товар.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    price: Decimal
    cashback_amount: Decimal
    payout_days: int
    review_required: bool = False
    receipt_required: bool = False
    product_url: str = Field(min_length=1)
    instruction_text: str = Field(min_length=1)
    available_slots: int = Field(ge=0)
    photo_file_ids: list[str] = Field(default_factory=list)
    admin_id: int

    @field_validator("price", "cashback_amount")
    @classmethod
    def validate_non_negative_amount(cls, value: Decimal) -> Decimal:
        """Проверяет, что денежная сумма не отрицательна.

        Args:
            value: Проверяемое значение цены или суммы кэшбэка.

        Returns:
            Проверенное значение без изменений.

        Raises:
            ValueError: Если значение отрицательное.
        """
        if value < 0:
            raise ValueError("Сумма не может быть отрицательной")
        return value

    @field_validator("payout_days")
    @classmethod
    def validate_payout_days(cls, value: int) -> int:
        """Проверяет, что срок выплаты — положительное число дней.

        Args:
            value: Проверяемое количество дней до выплаты.

        Returns:
            Проверенное значение без изменений.

        Raises:
            ValueError: Если значение меньше или равно нулю.
        """
        if value <= 0:
            raise ValueError("Срок выплаты должен быть положительным числом дней")
        return value


class ProductUpdateDTO(ProductCreateDTO):
    """Данные для полного редактирования существующего товара.

    Наследует все поля от `ProductCreateDTO` и дополнительно содержит
    идентификатор редактируемого товара.

    Attributes:
        product_id: Внутренний идентификатор редактируемого товара.
    """

    product_id: int
