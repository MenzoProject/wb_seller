"""Доменная сущность банка, используемого в реквизитах пользователей."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Bank:
    """Банк, доступный для выбора при сохранении реквизитов пользователя.

    Attributes:
        id: Внутренний идентификатор банка. `None` для ещё не сохранённой
            в базе данных сущности.
        name: Название банка, отображаемое пользователю.
        is_active: Признак того, что банк доступен для выбора в текущий момент.
    """

    id: int | None
    name: str
    is_active: bool = True
