"""Интерфейс репозитория для работы с реквизитами пользователей и банками.

Банки тесно связаны с реквизитами (используются исключительно как
справочник при их заполнении), поэтому методы работы со справочником
банков включены в этот же интерфейс.
"""

from __future__ import annotations

from typing import Protocol

from src.domain.entities.bank import Bank
from src.domain.entities.requisites import UserRequisites


class RequisitesRepository(Protocol):
    """Абстракция доступа к данным реквизитов и банков, не зависящая от СУБД."""

    async def get_by_id(self, requisites_id: int) -> UserRequisites | None:
        """Возвращает набор реквизитов по внутреннему идентификатору.

        Args:
            requisites_id: Внутренний идентификатор набора реквизитов.

        Returns:
            Найденные реквизиты либо None, если они не существуют.
        """

    async def list_by_user(self, user_id: int) -> list[UserRequisites]:
        """Возвращает все сохранённые наборы реквизитов пользователя.

        Args:
            user_id: Внутренний идентификатор пользователя.

        Returns:
            Список реквизитов пользователя, упорядоченный по дате создания
            (новые вначале).
        """

    async def get_default_for_user(self, user_id: int) -> UserRequisites | None:
        """Возвращает набор реквизитов пользователя, используемый по умолчанию.

        Args:
            user_id: Внутренний идентификатор пользователя.

        Returns:
            Реквизиты с признаком is_default=True либо None, если такие не заданы.
        """

    async def create(self, requisites: UserRequisites) -> UserRequisites:
        """Создаёт новый набор реквизитов пользователя.

        Args:
            requisites: Доменная сущность реквизитов без присвоенного `id`.

        Returns:
            Созданные реквизиты с присвоенным внутренним идентификатором.
        """

    async def update(self, requisites: UserRequisites) -> UserRequisites:
        """Обновляет данные существующего набора реквизитов.

        Args:
            requisites: Доменная сущность реквизитов с заполненным `id`.

        Returns:
            Обновлённая сущность реквизитов.

        Raises:
            EntityNotFoundError: Если реквизиты с указанным `id` не найдены.
        """

    async def delete(self, requisites_id: int) -> None:
        """Удаляет набор реквизитов пользователя.

        Args:
            requisites_id: Внутренний идентификатор удаляемых реквизитов.
        """

    async def unset_default_for_user(
        self, user_id: int, exclude_id: int | None = None
    ) -> None:
        """Снимает признак использования по умолчанию со всех реквизитов пользователя.

        Используется перед назначением нового набора реквизитов по умолчанию,
        чтобы гарантировать, что у пользователя есть не более одного набора
        реквизитов по умолчанию.

        Args:
            user_id: Внутренний идентификатор пользователя.
            exclude_id: Идентификатор набора реквизитов, который не нужно изменять.
        """

    async def list_active_banks(self) -> list[Bank]:
        """Возвращает список банков, доступных для выбора пользователем.

        Returns:
            Список активных банков, упорядоченный по названию.
        """

    async def get_bank_by_id(self, bank_id: int) -> Bank | None:
        """Возвращает банк по внутреннему идентификатору.

        Args:
            bank_id: Внутренний идентификатор банка.

        Returns:
            Найденный банк либо None, если банк не существует.
        """

    async def list_all_banks(self) -> list[Bank]:
        """Возвращает полный справочник банков (включая деактивированные).

        Используется панелью администратора, где нужно видеть и уметь
        включать обратно ранее деактивированные банки.

        Returns:
            Список всех банков, упорядоченный по названию.
        """

    async def get_bank_by_name(self, name: str) -> Bank | None:
        """Возвращает банк по точному названию (без учёта регистра).

        Args:
            name: Название банка для поиска.

        Returns:
            Найденный банк либо None, если банк с таким названием не существует.
        """

    async def create_bank(self, name: str) -> Bank:
        """Добавляет новый банк в справочник в активном состоянии.

        Args:
            name: Название нового банка.

        Returns:
            Созданная доменная сущность банка.

        Raises:
            BankNameAlreadyExistsError: Если банк с таким названием уже
                существует (обнаружено на уровне уникального ограничения БД).
        """

    async def set_bank_active(self, bank_id: int, is_active: bool) -> Bank:
        """Включает либо отключает банк для выбора пользователями.

        Args:
            bank_id: Внутренний идентификатор банка.
            is_active: Новое значение признака доступности банка.

        Returns:
            Обновлённая доменная сущность банка.

        Raises:
            EntityNotFoundError: Если банк с указанным `id` не найден.
        """
