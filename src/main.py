"""Точка входа приложения.

Загружает конфигурацию, инициализирует логирование, поднимает подключение
к базе данных и Redis, собирает DI-контейнер, регистрирует middlewares и
роутеры бота, запускает планировщик APScheduler (ежедневная проверка
заявок, готовых к выплате) и запускает long polling.
"""

from __future__ import annotations

import asyncio
import logging

from src.bot.bot_instance import (
    create_bot,
    create_dispatcher,
    create_fsm_storage,
    create_redis_client,
)
from src.bot.di.container import DIContainer
from src.bot.handlers.admin import get_admin_router
from src.bot.handlers.user import get_user_router
from src.bot.middlewares.db_session_middleware import DbSessionMiddleware
from src.bot.middlewares.logging_middleware import LoggingMiddleware
from src.bot.middlewares.services_middleware import ServicesMiddleware
from src.bot.middlewares.throttling_middleware import ThrottlingMiddleware
from src.bot.middlewares.user_registration_middleware import UserRegistrationMiddleware
from src.config.settings import AppSettings, get_settings
from src.infrastructure.database.engine import Database
from src.infrastructure.scheduler.scheduler import create_scheduler, register_payment_due_job
from src.logging_config.logger import configure_logging

logger = logging.getLogger(__name__)


def _mask_secret(value: str, visible_chars: int = 4) -> str:
    """Маскирует секретное значение, оставляя видимыми несколько символов.

    Args:
        value: Исходное секретное значение.
        visible_chars: Количество символов в конце строки, которые
            останутся видимыми.

    Returns:
        Маскированная строка вида '****abcd'.
    """
    if len(value) <= visible_chars:
        return "*" * len(value)
    return f"{'*' * (len(value) - visible_chars)}{value[-visible_chars:]}"


def _log_startup_banner(settings: AppSettings) -> None:
    """Выводит в лог сводную информацию о загруженной конфигурации.

    Args:
        settings: Полностью инициализированные настройки приложения.
    """
    logger.info("=" * 70)
    logger.info("Запуск приложения: %s", settings.app_name)
    logger.info("Окружение: %s", settings.app_env)
    logger.info("Telegram Bot Token: %s", _mask_secret(settings.bot.token))
    logger.info("Администраторы бота (ID): %s", settings.bot.admin_ids)
    logger.info(
        "База данных: %s@%s:%s/%s",
        settings.database.user,
        settings.database.host,
        settings.database.port,
        settings.database.db,
    )
    logger.info("Redis: %s:%s/%s", settings.redis.host, settings.redis.port, settings.redis.db)
    logger.info("=" * 70)


async def main() -> None:
    """Асинхронная точка входа приложения.

    Инициализирует конфигурацию, логирование, подключение к базе данных и
    Redis, собирает бота со всеми middlewares и роутерами и запускает
    обработку обновлений Telegram методом long polling.
    """
    settings = get_settings()
    configure_logging(settings)
    _log_startup_banner(settings)

    database = Database(settings.database)
    if not await database.check_connection():
        logger.error(
            "Не удалось подключиться к базе данных по адресу %s:%s. "
            "Проверьте настройки подключения и доступность PostgreSQL. "
            "Приложение будет остановлено.",
            settings.database.host,
            settings.database.port,
        )
        return

    container = DIContainer(settings, database)

    redis_client = create_redis_client(settings)
    storage = create_fsm_storage(redis_client, settings)

    bot = create_bot(settings)
    dispatcher = create_dispatcher(storage)

    # Settings и хранилище FSM доступны в хендлерах и фильтрах как именованные
    # параметры workflow-данных диспетчера (например, IsAdminFilter, а также
    # обработчики административного одобрения/повтора заявки, которым
    # требуется программно управлять FSM-состоянием другого пользователя).
    dispatcher["settings"] = settings
    dispatcher["fsm_storage"] = storage

    # Middlewares регистрируются как outer-middlewares уровня Update, что
    # гарантирует их срабатывание для любого типа апдейта (сообщение,
    # callback-запрос и т.д.). Порядок регистрации важен: он определяет
    # порядок выполнения кода "до" вызова следующего звена цепочки.
    dispatcher.update.outer_middleware(LoggingMiddleware())
    dispatcher.update.outer_middleware(ThrottlingMiddleware())
    dispatcher.update.outer_middleware(DbSessionMiddleware(database))
    dispatcher.update.outer_middleware(ServicesMiddleware(container))
    dispatcher.update.outer_middleware(UserRegistrationMiddleware())

    dispatcher.include_router(get_user_router())
    dispatcher.include_router(get_admin_router(settings.bot.admin_ids))

    scheduler = create_scheduler(settings)
    register_payment_due_job(scheduler, bot, container, settings)

    try:
        await bot.delete_webhook(drop_pending_updates=settings.bot.drop_pending_updates)
        scheduler.start()
        logger.info("Планировщик APScheduler запущен")
        logger.info("Бот успешно запущен, начинается обработка обновлений (long polling)...")
        await dispatcher.start_polling(
            bot, allowed_updates=dispatcher.resolve_used_update_types()
        )
    finally:
        logger.info("Остановка бота, закрытие соединений...")
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await redis_client.aclose()
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
