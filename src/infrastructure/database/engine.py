"""Инициализация асинхронного движка SQLAlchemy и фабрики сессий.

Класс `Database` инкапсулирует создание `AsyncEngine` и
`async_sessionmaker`, а также предоставляет асинхронный контекстный
менеджер для получения сессии с автоматическим commit/rollback.
Это единственная точка создания подключения к PostgreSQL в проекте.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import DatabaseSettings

logger = logging.getLogger(__name__)


class Database:
    """Инкапсулирует асинхронный движок и фабрику сессий SQLAlchemy.

    Экземпляр этого класса создаётся один раз при старте приложения и
    передаётся в DI-контейнер, откуда middleware пробрасывает сессии
    в обработчики бота.
    """

    def __init__(self, settings: DatabaseSettings) -> None:
        """Инициализирует движок и фабрику сессий на основе настроек БД.

        Args:
            settings: Настройки подключения к PostgreSQL.
        """
        self._engine: AsyncEngine = create_async_engine(
            settings.dsn,
            echo=settings.echo,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_pre_ping=True,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Возвращает асинхронный движок SQLAlchemy.

        Returns:
            Экземпляр AsyncEngine, привязанный к настроенной базе данных.
        """
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Возвращает фабрику асинхронных сессий SQLAlchemy.

        Returns:
            Фабрика async_sessionmaker для создания новых сессий.
        """
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Предоставляет асинхронную сессию с автоматическим commit/rollback.

        При успешном выполнении блока `async with` изменения фиксируются
        (`commit`). При возникновении исключения выполняется откат
        (`rollback`), после чего исключение пробрасывается дальше.
        Сессия закрывается в любом случае.

        Yields:
            Активная асинхронная сессия SQLAlchemy.
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def check_connection(self) -> bool:
        """Проверяет доступность базы данных простым запросом.

        Returns:
            True, если соединение с базой данных установлено успешно.
        """
        from sqlalchemy import text

        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            logger.exception("Не удалось установить соединение с базой данных")
            return False

    async def dispose(self) -> None:
        """Корректно закрывает все соединения движка при остановке приложения."""
        await self._engine.dispose()
        logger.info("Соединения с базой данных закрыты")
