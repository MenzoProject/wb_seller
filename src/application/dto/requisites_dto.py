"""DTO для операций с платёжными реквизитами пользователя."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateRequisitesDTO(BaseModel):
    """Данные для сохранения нового набора реквизитов пользователя.

    Attributes:
        user_id: Внутренний идентификатор пользователя.
        full_name: ФИО получателя выплаты.
        phone: Номер телефона, привязанный к банку для перевода.
        bank_id: Внутренний идентификатор выбранного банка.
        is_default: Использовать ли эти реквизиты по умолчанию.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: int
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=32)
    bank_id: int
    is_default: bool = False


class UpdateRequisitesDTO(BaseModel):
    """Данные для редактирования существующего набора реквизитов.

    Attributes:
        requisites_id: Внутренний идентификатор редактируемых реквизитов.
        user_id: Внутренний идентификатор владельца реквизитов (для проверки прав).
        full_name: ФИО получателя выплаты.
        phone: Номер телефона, привязанный к банку для перевода.
        bank_id: Внутренний идентификатор выбранного банка.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    requisites_id: int
    user_id: int
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=32)
    bank_id: int
