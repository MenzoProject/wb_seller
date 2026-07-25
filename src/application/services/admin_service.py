"""Сервис бизнес-логики работы с администраторами бота."""

from __future__ import annotations

import logging

from src.domain.entities.admin import Admin
from src.infrastructure.repositories.interfaces.admin_repository import AdminRepository

logger = logging.getLogger(__name__)


class AdminService:
    """Сервис, инкапсулирующий бизнес-логику работы с администраторами бота.

    Список Telegram ID администраторов задаётся конфигурацией
    (`settings.bot.admin_ids`) и является источником истины о том, кто
    имеет доступ к панели администратора (эту проверку выполняет
    `AdminAccessMiddleware`). Данный сервис отвечает лишь за то, чтобы у
    каждого администратора существовала соответствующая запись в базе
    данных — она нужна как внутренний идентификатор для внешних ключей
    (кто создал товар, кто подтвердил выплату и т.д.).
    """

    def __init__(self, admin_repository: AdminRepository) -> None:
        """Инициализирует сервис репозиторием администраторов.

        Args:
            admin_repository: Реализация репозитория администраторов.
        """
        self._admin_repository = admin_repository

    async def get_or_create(self, telegram_id: int, full_name: str) -> Admin:
        """Возвращает существующего администратора либо регистрирует нового.

        Args:
            telegram_id: Уникальный идентификатор администратора в Telegram
                (уже проверенный `AdminAccessMiddleware` на принадлежность
                к списку `settings.bot.admin_ids`).
            full_name: Текущее полное имя администратора в Telegram.

        Returns:
            Доменная сущность администратора — существующая или только что созданная.
        """
        existing_admin = await self._admin_repository.get_by_telegram_id(telegram_id)
        if existing_admin is not None:
            return existing_admin

        new_admin = Admin(id=None, telegram_id=telegram_id, full_name=full_name)
        created_admin = await self._admin_repository.create(new_admin)
        logger.info("Зарегистрирован новый администратор telegram_id=%s", telegram_id)
        return created_admin
