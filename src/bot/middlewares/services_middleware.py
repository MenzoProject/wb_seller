"""Middleware, собирающее сервисы приложения для текущей сессии БД."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.bot.di.container import DIContainer


class ServicesMiddleware(BaseMiddleware):
    """Собирает сервисы приложения и добавляет их в контекст обработчика.

    Должен быть зарегистрирован после `DbSessionMiddleware`, так как
    использует сессию БД, помещённую им в `data["session"]`. Каждый сервис
    добавляется в `data` под собственным ключом (`user_service`,
    `product_service` и т.д.), что позволяет обработчикам запрашивать
    только нужные им сервисы через типизированные параметры функции.
    """

    def __init__(self, container: DIContainer) -> None:
        """Инициализирует middleware DI-контейнером приложения.

        Args:
            container: Контейнер внедрения зависимостей приложения.
        """
        self._container = container

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Собирает сервисы для текущей сессии и добавляет их в данные обработчика.

        Args:
            handler: Следующий обработчик в цепочке middlewares.
            event: Обрабатываемый объект апдейта Telegram.
            data: Словарь контекстных данных, передаваемых обработчику.

        Returns:
            Результат выполнения следующего обработчика в цепочке.
        """
        session = data["session"]
        services = self._container.build_services(session)

        data["user_service"] = services.user_service
        data["admin_service"] = services.admin_service
        data["product_service"] = services.product_service
        data["application_service"] = services.application_service
        data["payment_service"] = services.payment_service
        data["requisites_service"] = services.requisites_service
        data["statistics_service"] = services.statistics_service

        return await handler(event, data)
