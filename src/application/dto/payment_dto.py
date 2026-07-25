"""DTO для операций с выплатами по заявкам."""

from __future__ import annotations

from pydantic import BaseModel


class MarkPaymentPaidDTO(BaseModel):
    """Данные для отметки выплаты по заявке как произведённой.

    Attributes:
        application_id: Внутренний идентификатор заявки, по которой
            произведена выплата.
        admin_id: Внутренний идентификатор администратора, подтвердившего выплату.
    """

    application_id: int
    admin_id: int
