"""ORM-модель заявки реселлера на выкуп товара."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums.application_status import ApplicationStatus
from src.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.payment import Payment
    from src.infrastructure.database.models.product import Product
    from src.infrastructure.database.models.user import User
    from src.infrastructure.database.models.user_requisites import UserRequisites


class Application(TimestampMixin, Base):
    """Заявка пользователя на выкуп товара с последующим кэшбэком.

    Заявка последовательно проходит через статусы, описанные в
    `src.domain.enums.application_status.ApplicationStatus`. Текущий статус
    определяет, какое действие ожидается от пользователя или администратора.

    Attributes:
        id: Внутренний идентификатор заявки.
        user_id: Идентификатор пользователя, оформившего заявку.
        product_id: Идентификатор товара, на который оформлена заявка.
        status: Текущий статус заявки.
        article: Артикул товара на маркетплейсе, указанный пользователем.
        order_screenshot_file_id: file_id скриншота подтверждения заказа.
        receipt_link: Ссылка на чек (кассовый чек, чек ЮKassa и т.д.).
        review_screenshot_file_id: file_id скриншота оставленного отзыва.
        requisites_id: Идентификатор реквизитов, выбранных для выплаты.
        admin_comment: Комментарий администратора (причина отклонения или
            запроса повторной отправки данных).
        payout_due_date: Расчётная дата, на которую должна быть произведена
            выплата (вычисляется как дата перехода в WAIT_PAYMENT + payout_days
            товара).
    """

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            name="application_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ApplicationStatus.NEW,
        server_default=ApplicationStatus.NEW.value,
        nullable=False,
        index=True,
    )
    article: Mapped[str | None] = mapped_column(String(128), nullable=True)
    order_screenshot_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_screenshot_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requisites_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_requisites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    payout_due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    user: Mapped["User"] = relationship(back_populates="applications")
    product: Mapped["Product"] = relationship(back_populates="applications")
    requisites: Mapped["UserRequisites | None"] = relationship(back_populates="applications")
    payment: Mapped["Payment | None"] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:
        """Возвращает техническое представление объекта для логов и отладки.

        Returns:
            Строка с ключевыми полями заявки.
        """
        return (
            f"Application(id={self.id}, user_id={self.user_id}, "
            f"product_id={self.product_id}, status={self.status.value})"
        )
