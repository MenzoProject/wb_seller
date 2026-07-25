"""Middleware ограничения частоты запросов (throttling) от одного пользователя."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

_CLEANUP_THRESHOLD = 5_000
_STALE_ENTRY_SECONDS = 300.0


class ThrottlingMiddleware(BaseMiddleware):
    """Ограничивает частоту обработки апдейтов от одного пользователя.

    Простая in-memory реализация на основе минимального интервала между
    последовательными запросами одного пользователя. Для распределённого
    развёртывания с несколькими инстансами бота потребовалась бы
    реализация на Redis, но для одного инстанса локального ограничителя
    достаточно и он не добавляет дополнительной задержки на сетевой запрос.
    """

    def __init__(self, rate_limit_seconds: float = 0.7) -> None:
        """Инициализирует middleware минимальным интервалом между запросами.

        Args:
            rate_limit_seconds: Минимальный интервал в секундах между
                последовательными запросами одного пользователя.
        """
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call_at: dict[int, float] = {}

    def _cleanup_stale_entries(self, now: float) -> None:
        """Удаляет устаревшие записи, чтобы словарь не рос неограниченно.

        Args:
            now: Текущее значение монотонного времени.
        """
        if len(self._last_call_at) < _CLEANUP_THRESHOLD:
            return
        stale_keys = [
            user_id
            for user_id, last_call in self._last_call_at.items()
            if now - last_call > _STALE_ENTRY_SECONDS
        ]
        for user_id in stale_keys:
            del self._last_call_at[user_id]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Пропускает запрос дальше по цепочке, если интервал ограничения соблюдён.

        Args:
            handler: Следующий обработчик в цепочке middlewares.
            event: Обрабатываемый объект апдейта Telegram.
            data: Словарь контекстных данных, передаваемых обработчику.

        Returns:
            Результат выполнения следующего обработчика в цепочке, либо
            `None`, если запрос отклонён из-за превышения частоты.
        """
        telegram_user = data.get("event_from_user")
        if telegram_user is None:
            return await handler(event, data)

        now = time.monotonic()
        self._cleanup_stale_entries(now)

        last_call = self._last_call_at.get(telegram_user.id)
        if last_call is not None and (now - last_call) < self._rate_limit_seconds:
            if isinstance(event, CallbackQuery):
                await event.answer("⏳ Слишком часто, подождите немного.")
            return None

        self._last_call_at[telegram_user.id] = now
        return await handler(event, data)
