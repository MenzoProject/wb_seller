"""Интерфейс репозитория для работы с заявками на выкуп товара."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from src.domain.entities.application import Application
from src.domain.enums.application_status import ApplicationStatus


class ApplicationRepository(Protocol):
    """Абстракция доступа к данным заявок, не зависящая от СУБД."""

    async def get_by_id(self, application_id: int) -> Application | None:
        """Возвращает заявку по внутреннему идентификатору.

        Args:
            application_id: Внутренний идентификатор заявки.

        Returns:
            Найденная заявка либо None, если заявка не существует.
        """

    async def create(self, application: Application) -> Application:
        """Создаёт новую заявку в хранилище данных.

        Args:
            application: Доменная сущность заявки без присвоенного `id`.

        Returns:
            Созданная заявка с присвоенным внутренним идентификатором.
        """

    async def update(self, application: Application) -> Application:
        """Обновляет данные существующей заявки.

        Args:
            application: Доменная сущность заявки с заполненным `id`.

        Returns:
            Обновлённая сущность заявки.

        Raises:
            EntityNotFoundError: Если заявка с указанным `id` не найдена.
        """

    async def list_by_user(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Application]:
        """Возвращает страницу заявок конкретного пользователя.

        Args:
            user_id: Внутренний идентификатор пользователя.
            limit: Максимальное количество заявок в результате.
            offset: Количество заявок, которые нужно пропустить.

        Returns:
            Список заявок пользователя, упорядоченный по дате создания
            (новые вначале).
        """

    async def list_by_status(
        self, status: ApplicationStatus, limit: int = 50, offset: int = 0
    ) -> list[Application]:
        """Возвращает страницу заявок с указанным статусом.

        Используется панелью администратора для отображения очереди заявок,
        ожидающих проверки.

        Args:
            status: Статус заявок для фильтрации.
            limit: Максимальное количество заявок в результате.
            offset: Количество заявок, которые нужно пропустить.

        Returns:
            Список заявок с указанным статусом, упорядоченный по дате
            создания (старые вначале, для порядка обработки FIFO).
        """

    async def list_due_for_payout(self, as_of: date) -> list[Application]:
        """Возвращает заявки, ожидающие выплаты, у которых наступила дата выплаты.

        Используется планировщиком APScheduler для ежедневного уведомления
        администраторов о заявках, готовых к выплате.

        Args:
            as_of: Дата, относительно которой производится поиск (обычно
                текущая дата).

        Returns:
            Список заявок в статусе WAIT_PAYMENT с payout_due_date <= as_of.
        """

    async def count_by_status(self, status: ApplicationStatus) -> int:
        """Возвращает количество заявок с указанным статусом.

        Args:
            status: Статус заявок для подсчёта.

        Returns:
            Количество заявок в указанном статусе.
        """

    async def get_active_application(
        self, user_id: int, product_id: int
    ) -> Application | None:
        """Возвращает активную (не завершённую) заявку пользователя на указанный товар.

        Используется для предотвращения повторного оформления заявки на тот
        же товар, пока предыдущая заявка ещё не завершена (не в статусе
        PAID или REJECTED).

        Args:
            user_id: Внутренний идентификатор пользователя.
            product_id: Внутренний идентификатор товара.

        Returns:
            Активная заявка либо None, если таких заявок нет.
        """
