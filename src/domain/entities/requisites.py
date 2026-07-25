"""Доменная сущность платёжных реквизитов пользователя."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from src.domain.exceptions.requisites_exceptions import InvalidRequisitesDataError

_PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-()]{10,20}$")


@dataclass(slots=True)
class UserRequisites:
    """Платёжные реквизиты пользователя, сохранённые для повторного использования.

    Attributes:
        id: Внутренний идентификатор набора реквизитов. `None` для ещё не
            сохранённой в базе данных сущности.
        user_id: Идентификатор владельца реквизитов.
        full_name: ФИО получателя выплаты.
        phone: Номер телефона, привязанный к банку для перевода.
        bank_id: Идентификатор банка получателя.
        is_default: Признак использования данного набора реквизитов по умолчанию.
        created_at: Дата и время сохранения реквизитов.
    """

    id: int | None
    user_id: int
    full_name: str
    phone: str
    bank_id: int
    is_default: bool = False
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Проверяет корректность ФИО и номера телефона сразу после создания сущности.

        Raises:
            InvalidRequisitesDataError: Если ФИО пустое либо телефон не
                соответствует ожидаемому формату.
        """
        self.full_name = self.full_name.strip()
        self.phone = self.phone.strip()
        if not self.full_name:
            raise InvalidRequisitesDataError("ФИО получателя не может быть пустым")
        if len(self.full_name) < 3:
            raise InvalidRequisitesDataError("ФИО получателя указано слишком коротко")
        if not _PHONE_PATTERN.match(self.phone):
            raise InvalidRequisitesDataError(
                f"Номер телефона '{self.phone}' имеет некорректный формат"
            )

    def make_default(self) -> None:
        """Помечает данный набор реквизитов как используемый по умолчанию."""
        self.is_default = True

    def unmark_default(self) -> None:
        """Снимает с набора реквизитов признак использования по умолчанию."""
        self.is_default = False
