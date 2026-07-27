"""seed default banks

Revision ID: 0003_seed_banks
Revises: 0002_add_receipt_required
Create Date: 2026-07-26 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_seed_banks"
down_revision: Union[str, None] = "0002_add_receipt_required"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BANKS_TABLE = sa.table(
    "banks",
    sa.column("name", sa.String),
    sa.column("is_active", sa.Boolean),
)

_DEFAULT_BANK_NAMES: tuple[str, ...] = (
    "Сбербанк",
    "Т-Банк (Тинькофф)",
    "Альфа-Банк",
    "ВТБ",
    "Озон Банк",
    "Райффайзенбанк",
    "Газпромбанк",
    "Совкомбанк",
)


def upgrade() -> None:
    """Наполняет справочник банков стартовым набором наиболее востребованных банков.

    Без этих данных раздел «Реквизиты» пользовательского бота
    неработоспособен: пользователю не из чего выбрать банк при сохранении
    реквизитов для выплаты. Список банков в дальнейшем может быть
    расширен администратором напрямую через базу данных (управление
    справочником банков через интерфейс бота не входит в текущий объём
    проекта).
    """
    op.bulk_insert(
        _BANKS_TABLE,
        [{"name": name, "is_active": True} for name in _DEFAULT_BANK_NAMES],
    )


def downgrade() -> None:
    """Удаляет ранее добавленный стартовый набор банков."""
    banks_table = sa.table("banks", sa.column("name", sa.String))
    op.execute(
        banks_table.delete().where(banks_table.c.name.in_(_DEFAULT_BANK_NAMES))
    )
