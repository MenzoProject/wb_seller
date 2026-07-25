"""Доменная сущность администратора бота."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Admin:
    """Администратор, имеющий доступ к панели управления бота.

    Attributes:
        id: Внутренний идентификатор администратора. `None` для ещё не
            сохранённой в базе данных сущности.
        telegram_id: Уникальный идентификатор администратора в Telegram.
        full_name: Полное имя администратора.
        is_super_admin: Признак расширенных прав администратора.
        created_at: Дата и время регистрации администратора в системе.
    """

    id: int | None
    telegram_id: int
    full_name: str
    is_super_admin: bool = False
    created_at: datetime | None = None
