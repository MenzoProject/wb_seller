"""DTO для операций жизненного цикла заявки на выкуп товара."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateApplicationDTO(BaseModel):
    """Данные для создания новой заявки при выборе товара пользователем.

    Attributes:
        user_id: Внутренний идентификатор пользователя.
        product_id: Внутренний идентификатор выбранного товара.
    """

    user_id: int
    product_id: int


class SubmitArticleDTO(BaseModel):
    """Данные для фиксации артикула товара, отправленного пользователем.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        article: Артикул товара на маркетплейсе.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    application_id: int
    article: str = Field(min_length=1, max_length=128)


class SubmitOrderScreenshotDTO(BaseModel):
    """Данные для фиксации скриншота подтверждения заказа.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        file_id: Идентификатор файла скриншота в Telegram.
    """

    application_id: int
    file_id: str = Field(min_length=1)


class ApproveOrderDTO(BaseModel):
    """Данные для подтверждения заказа администратором.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        admin_id: Внутренний идентификатор администратора, подтвердившего заказ.
    """

    application_id: int
    admin_id: int


class RequestOrderScreenshotResendDTO(BaseModel):
    """Данные для запроса повторной отправки скриншота заказа.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        admin_id: Внутренний идентификатор администратора, запросившего повтор.
        reason: Причина, по которой скриншот не был принят.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    application_id: int
    admin_id: int
    reason: str = Field(min_length=1)


class RejectApplicationDTO(BaseModel):
    """Данные для отклонения заявки администратором.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        admin_id: Внутренний идентификатор администратора, отклонившего заявку.
        reason: Причина отклонения заявки.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    application_id: int
    admin_id: int
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def validate_reason_not_blank(cls, value: str) -> str:
        """Проверяет, что причина отклонения не пуста после удаления пробелов.

        Args:
            value: Проверяемая причина отклонения.

        Returns:
            Проверенное значение без изменений.

        Raises:
            ValueError: Если причина состоит только из пробельных символов.
        """
        if not value.strip():
            raise ValueError("Причина отклонения не может быть пустой")
        return value


class ConfirmReceiveDTO(BaseModel):
    """Данные для фиксации подтверждения получения товара пользователем.

    Attributes:
        application_id: Внутренний идентификатор заявки.
    """

    application_id: int


class SubmitReviewScreenshotDTO(BaseModel):
    """Данные для фиксации скриншота оставленного отзыва.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        file_id: Идентификатор файла скриншота отзыва в Telegram.
    """

    application_id: int
    file_id: str = Field(min_length=1)


class SubmitReceiptLinkDTO(BaseModel):
    """Данные для фиксации ссылки на чек оплаты.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        receipt_link: Ссылка на электронный чек об оплате.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    application_id: int
    receipt_link: str = Field(min_length=1)


class AssignRequisitesDTO(BaseModel):
    """Данные для привязки выбранных реквизитов к заявке.

    Attributes:
        application_id: Внутренний идентификатор заявки.
        requisites_id: Внутренний идентификатор набора реквизитов пользователя.
    """

    application_id: int
    requisites_id: int


class CancelApplicationDTO(BaseModel):
    """Данные для отмены заявки самим пользователем до её проверки администратором.

    Attributes:
        application_id: Внутренний идентификатор отменяемой заявки.
        user_id: Внутренний идентификатор пользователя (для проверки прав).
    """

    application_id: int
    user_id: int
