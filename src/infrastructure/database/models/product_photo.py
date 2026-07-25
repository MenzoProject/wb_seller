"""ORM-модель фотографии товара."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.product import Product


class ProductPhoto(CreatedAtMixin, Base):
    """Фотография товара, хранящаяся по file_id Telegram.

    Товар может содержать несколько фотографий, отображаемых в каталоге
    в порядке, заданном полем `position`.

    Attributes:
        id: Внутренний идентификатор фотографии.
        product_id: Идентификатор товара, которому принадлежит фотография.
        file_id: Идентификатор файла в Telegram (`file_id`), используемый
            для повторной отправки фотографии без повторной загрузки.
        position: Порядковый номер фотографии в галерее товара.
    """

    __tablename__ = "product_photos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    product: Mapped["Product"] = relationship(back_populates="photos")

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями фотографии товара.
        """
        return (
            f"ProductPhoto(id={self.id}, product_id={self.product_id}, "
            f"position={self.position})"
        )
