"""Фильтр проверки текущего статуса заявки.

Используется для защиты обработчиков административных действий над
заявкой (подтверждение, отклонение, запрос повтора) от повторного
срабатывания на уже обработанной заявке — например, если два
администратора одновременно открыли одну и ту же заявку и один из них
уже принял решение.
"""

from __future__ import annotations

from aiogram.types import CallbackQuery

from src.application.services.application_service import ApplicationService
from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.application_exceptions import ApplicationNotFoundError


class ApplicationStatusFilter:
    """Фильтр, пропускающий callback только если заявка находится в одном из статусов.

    Ожидает, что идентификатор заявки уже извлечён из данных callback'а на
    предыдущем этапе обработки (например, через `CallbackData`-фабрику) и
    доступен в контекстных данных обработчика под ключом `application_id`.
    """

    def __init__(self, *allowed_statuses: ApplicationStatus) -> None:
        """Инициализирует фильтр набором допустимых статусов заявки.

        Args:
            allowed_statuses: Статусы, при которых событие должно быть
                пропущено фильтром.
        """
        self._allowed_statuses = allowed_statuses

    async def __call__(
        self,
        event: CallbackQuery,
        application_id: int,
        application_service: ApplicationService,
    ) -> bool:
        """Проверяет, что заявка существует и находится в одном из допустимых статусов.

        Args:
            event: Обрабатываемый callback-запрос.
            application_id: Внутренний идентификатор проверяемой заявки.
            application_service: Сервис заявок, внедряемый aiogram из
                контекстных данных, собранных `ServicesMiddleware`.

        Returns:
            True, если заявка найдена и её статус входит в список
            допустимых, иначе False.
        """
        try:
            application = await application_service.get_application(application_id)
        except ApplicationNotFoundError:
            await event.answer("Заявка не найдена.", show_alert=True)
            return False

        if application.status not in self._allowed_statuses:
            await event.answer(
                "Статус заявки уже был изменён другим администратором.", show_alert=True
            )
            return False

        return True
