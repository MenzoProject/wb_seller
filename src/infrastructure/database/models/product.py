"""ORM-модель товара каталога."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.application import Application
    from src.infrastructure.database.models.product_photo import ProductPhoto


class Product(TimestampMixin, Base):
    """Товар, доступный для оформления заявки на выкуп с кэшбэком.

    Attributes:
        id: Внутренний идентификатор товара.
        title: Название товара.
        description: Описание товара для отображения в каталоге.
        price: Цена, которую реселлер платит при заказе товара.
        cashback_amount: Сумма кэшбэка, выплачиваемая после выполнения условий.
        payout_days: Количество дней от выполнения условий до даты выплаты.
        review_required: Признак того, что для получения кэшбэка требуется отзыв.
        receipt_required: Признак того, что для получения кэшбэка требуется чек об оплате.
        product_url: Ссылка на карточку товара на маркетплейсе.
        instruction_text: Текстовая инструкция по оформлению заказа для этого товара.
        available_slots: Количество доступных для оформления заявок по товару.
        is_hidden: Признак скрытия товара из каталога (временно недоступен).
        is_deleted: Признак мягкого удаления товара (soft delete).
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cashback_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payout_days: Mapped[int] = mapped_column(Integer, nullable=False)
    review_required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    receipt_required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    product_url: Mapped[str] = mapped_column(Text, nullable=False)
    instruction_text: Mapped[str] = mapped_column(Text, nullable=False)
    available_slots: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False, index=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False, index=True
    )

    photos: Mapped[list["ProductPhoto"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductPhoto.position",
    )
    applications: Mapped[list["Application"]] = relationship(back_populates="product")

    @property
    def is_available(self) -> bool:
        """Признак того, что товар доступен для оформления новой заявки.

        Returns:
            True, если товар не скрыт, не удалён и имеет свободные слоты заявок.
        """
        return not self.is_hidden and not self.is_deleted and self.available_slots > 0

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями товара.
        """
        return (
            f"Product(id={self.id}, title={self.title!r}, price={self.price}, "
            f"available_slots={self.available_slots}, is_hidden={self.is_hidden})"
        )
