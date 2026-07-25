"""Фабрики создания экземпляров Bot, Dispatcher и хранилища FSM-состояний."""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from src.config.settings import AppSettings


def create_bot(settings: AppSettings) -> Bot:
    """Создаёт экземпляр `Bot` aiogram, сконфигурированный по настройкам приложения.

    Args:
        settings: Полностью инициализированные настройки приложения.

    Returns:
        Экземпляр `Bot` с токеном и режимом разбора текста из конфигурации.
    """
    return Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode(settings.bot.parse_mode)),
    )


def create_redis_client(settings: AppSettings) -> Redis:
    """Создаёт асинхронный клиент Redis для хранения FSM-состояний.

    Args:
        settings: Полностью инициализированные настройки приложения.

    Returns:
        Асинхронный клиент Redis, подключённый по DSN из конфигурации.
    """
    return Redis.from_url(settings.redis.dsn, decode_responses=False)


def create_fsm_storage(redis_client: Redis, settings: AppSettings) -> RedisStorage:
    """Создаёт хранилище FSM-состояний aiogram на основе Redis.

    Args:
        redis_client: Асинхронный клиент Redis.
        settings: Полностью инициализированные настройки приложения (для TTL записей).

    Returns:
        Экземпляр `RedisStorage`, используемый диспетчером для хранения
        состояний и данных FSM между сообщениями пользователя.
    """
    return RedisStorage(
        redis=redis_client,
        state_ttl=settings.redis.fsm_ttl_seconds,
        data_ttl=settings.redis.fsm_ttl_seconds,
    )


def create_dispatcher(storage: RedisStorage) -> Dispatcher:
    """Создаёт диспетчер aiogram с переданным хранилищем FSM-состояний.

    Args:
        storage: Хранилище FSM-состояний.

    Returns:
        Экземпляр `Dispatcher`, готовый для регистрации middlewares и роутеров.
    """
    return Dispatcher(storage=storage)
