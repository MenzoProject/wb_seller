"""add receipt_required to products

Revision ID: 0002_add_receipt_required
Revises: 0001_initial_schema
Create Date: 2026-07-22 01:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_receipt_required"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет в таблицу products поле receipt_required.

    Поле определяет, требуется ли для получения кэшбэка по товару
    предоставление пользователем ссылки на чек об оплате — этот шаг
    является условным этапом процесса заявки (WAIT_RECEIPT_LINK), наряду
    с уже существующим review_required.
    """
    op.add_column(
        "products",
        sa.Column(
            "receipt_required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Удаляет поле receipt_required из таблицы products."""
    op.drop_column("products", "receipt_required")
