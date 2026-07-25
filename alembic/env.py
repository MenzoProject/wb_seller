"""Точка входа Alembic для генерации и применения миграций.

Использует асинхронный движок SQLAlchemy (asyncpg), URL подключения
берётся из настроек приложения (`src.config.settings.get_settings`),
а не из статического значения в `alembic.ini`, чтобы конфигурация базы
данных оставалась единой точкой правды во всём проекте.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.config.settings import get_settings
from src.infrastructure.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.dsn)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запускает миграции в offline-режиме (без подключения к БД).

    В этом режиме Alembic генерирует SQL-скрипт вместо непосредственного
    выполнения миграций, используя только URL подключения.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Настраивает контекст Alembic и выполняет миграции на активном соединении.

    Args:
        connection: Синхронное соединение, полученное через `run_sync`
            из асинхронного соединения SQLAlchemy.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запускает миграции в online-режиме через асинхронный движок SQLAlchemy."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
