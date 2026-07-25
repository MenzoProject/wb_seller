"""Интерфейс репозитория для работы с журналом (аудит-логом) действий."""

from __future__ import annotations

from typing import Protocol

from src.domain.entities.log import Log


class LogRepository(Protocol):
    """Абстракция доступа к данным журнала аудита, не зависящая от СУБД."""

    async def create(self, log: Log) -> Log:
        """Создаёт новую запись журнала.

        Args:
            log: Доменная сущность записи журнала без присвоенного `id`.

        Returns:
            Созданная запись журнала с присвоенным внутренним идентификатором.
        """

    async def list_by_entity(
        self, entity_type: str, entity_id: int, limit: int = 50
    ) -> list[Log]:
        """Возвращает историю действий, связанных с конкретной сущностью.

        Args:
            entity_type: Тип сущности (например, 'Application', 'Product').
            entity_id: Идентификатор сущности.
            limit: Максимальное количество записей в результате.

        Returns:
            Список записей журнала, упорядоченный по дате (новые вначале).
        """

    async def list_recent(self, limit: int = 50) -> list[Log]:
        """Возвращает последние записи журнала по всем сущностям.

        Args:
            limit: Максимальное количество записей в результате.

        Returns:
            Список последних записей журнала, упорядоченный по дате
            (новые вначале).
        """
