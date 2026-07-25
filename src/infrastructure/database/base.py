"""Базовые классы для ORM-моделей SQLAlchemy.

Содержит базовый декларативный класс `Base`, от которого наследуются все
модели проекта, а также переиспользуемые миксины для служебных полей
временных меток (`created_at`, `updated_at`).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый декларативный класс для всех ORM-моделей проекта.

    Все модели в `src.infrastructure.database.models` наследуются от этого
    класса, что позволяет Alembic и SQLAlchemy собирать единую метадату
    для автогенерации миграций.
    """


class CreatedAtMixin:
    """Миксин, добавляющий модели поле времени создания записи."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Дата и время создания записи",
    )


class TimestampMixin(CreatedAtMixin):
    """Миксин, добавляющий модели поля времени создания и обновления записи."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Дата и время последнего обновления записи",
    )
