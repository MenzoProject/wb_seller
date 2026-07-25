"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-22 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создаёт полную схему базы данных проекта."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column(
            "is_blocked",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column(
            "is_super_admin",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admins_telegram_id"), "admins", ["telegram_id"], unique=True)

    op.create_table(
        "banks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("cashback_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payout_days", sa.Integer(), nullable=False),
        sa.Column(
            "review_required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("instruction_text", sa.Text(), nullable=False),
        sa.Column(
            "available_slots",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "is_hidden",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_is_hidden"), "products", ["is_hidden"], unique=False)
    op.create_index(op.f("ix_products_is_deleted"), "products", ["is_deleted"], unique=False)

    op.create_table(
        "product_photos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.String(length=255), nullable=False),
        sa.Column(
            "position",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_product_photos_product_id"), "product_photos", ["product_id"], unique=False
    )

    op.create_table(
        "user_requisites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_id"], ["banks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_requisites_user_id"), "user_requisites", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_requisites_bank_id"), "user_requisites", ["bank_id"], unique=False
    )

    application_status_enum = postgresql.ENUM(
        "NEW",
        "WAIT_ORDER_SCREEN",
        "ORDER_ON_REVIEW",
        "ORDER_APPROVED",
        "WAIT_RECEIVE",
        "WAIT_REVIEW",
        "WAIT_RECEIPT_LINK",
        "WAIT_PAYMENT",
        "PAID",
        "REJECTED",
        name="application_status",
    )
    application_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "NEW",
                "WAIT_ORDER_SCREEN",
                "ORDER_ON_REVIEW",
                "ORDER_APPROVED",
                "WAIT_RECEIVE",
                "WAIT_REVIEW",
                "WAIT_RECEIPT_LINK",
                "WAIT_PAYMENT",
                "PAID",
                "REJECTED",
                name="application_status",
                create_type=False,
            ),
            server_default="NEW",
            nullable=False,
        ),
        sa.Column("article", sa.String(length=128), nullable=True),
        sa.Column("order_screenshot_file_id", sa.String(length=255), nullable=True),
        sa.Column("receipt_link", sa.Text(), nullable=True),
        sa.Column("review_screenshot_file_id", sa.String(length=255), nullable=True),
        sa.Column("requisites_id", sa.Integer(), nullable=True),
        sa.Column("admin_comment", sa.Text(), nullable=True),
        sa.Column("payout_due_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["requisites_id"], ["user_requisites.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_applications_product_id"), "applications", ["product_id"], unique=False
    )
    op.create_index(op.f("ix_applications_status"), "applications", ["status"], unique=False)
    op.create_index(
        op.f("ix_applications_requisites_id"), "applications", ["requisites_id"], unique=False
    )
    op.create_index(
        op.f("ix_applications_payout_due_date"),
        "applications",
        ["payout_due_date"],
        unique=False,
    )

    payment_status_enum = postgresql.ENUM("PENDING", "PAID", name="payment_status")
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("PENDING", "PAID", name="payment_status", create_type=False),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("paid_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["paid_by_admin_id"], ["admins.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(op.f("ix_payments_status"), "payments", ["status"], unique=False)

    op.create_table(
        "logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_logs_user_id"), "logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_logs_admin_id"), "logs", ["admin_id"], unique=False)
    op.create_index(op.f("ix_logs_action"), "logs", ["action"], unique=False)
    op.create_index(op.f("ix_logs_entity_type"), "logs", ["entity_type"], unique=False)


def downgrade() -> None:
    """Полностью откатывает схему базы данных, удаляя все созданные таблицы и типы."""
    op.drop_index(op.f("ix_logs_entity_type"), table_name="logs")
    op.drop_index(op.f("ix_logs_action"), table_name="logs")
    op.drop_index(op.f("ix_logs_admin_id"), table_name="logs")
    op.drop_index(op.f("ix_logs_user_id"), table_name="logs")
    op.drop_table("logs")

    op.drop_index(op.f("ix_payments_status"), table_name="payments")
    op.drop_table("payments")
    postgresql.ENUM(name="payment_status").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_applications_payout_due_date"), table_name="applications")
    op.drop_index(op.f("ix_applications_requisites_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_status"), table_name="applications")
    op.drop_index(op.f("ix_applications_product_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_user_id"), table_name="applications")
    op.drop_table("applications")
    postgresql.ENUM(name="application_status").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_user_requisites_bank_id"), table_name="user_requisites")
    op.drop_index(op.f("ix_user_requisites_user_id"), table_name="user_requisites")
    op.drop_table("user_requisites")

    op.drop_index(op.f("ix_product_photos_product_id"), table_name="product_photos")
    op.drop_table("product_photos")

    op.drop_index(op.f("ix_products_is_deleted"), table_name="products")
    op.drop_index(op.f("ix_products_is_hidden"), table_name="products")
    op.drop_table("products")

    op.drop_table("banks")

    op.drop_index(op.f("ix_admins_telegram_id"), table_name="admins")
    op.drop_table("admins")

    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
