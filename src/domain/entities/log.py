"""Доменная сущность записи журнала (аудит-лога) действий в системе."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Log:
    """Запись журнала действий пользователя или администратора.

    Attributes:
        id: Внутренний идентификатор записи журнала. `None` для ещё не
            сохранённой в базе данных сущности.
        user_id: Идентификатор пользователя, совершившего действие
            (может отсутствовать, если действие совершил администратор).
        admin_id: Идентификатор администратора, совершившего действие
            (может отсутствовать, если действие совершил пользователь).
        action: Краткий машиночитаемый код действия.
        entity_type: Тип сущности, к которой относится действие.
        entity_id: Идентификатор сущности, к которой относится действие.
        payload: Дополнительные структурированные данные о событии.
        created_at: Дата и время события.
    """

    id: int | None
    action: str
    entity_type: str
    user_id: int | None = None
    admin_id: int | None = None
    entity_id: int | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime | None = None
