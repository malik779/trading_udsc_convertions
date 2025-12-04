"""initial schema

Revision ID: 20251204_0001
Revises:
Create Date: 2025-12-04 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251204_0001"
down_revision = None
branch_labels = None
depends_on = None


network_enum = sa.Enum("ethereum", "bnb", "solana", name="network")
transaction_type_enum = sa.Enum("deposit", "withdrawal", name="transactiontype")
transaction_status_enum = sa.Enum("pending", "broadcasted", "confirmed", "failed", name="transactionstatus")


def upgrade() -> None:
    network_enum.create(op.get_bind(), checkfirst=True)
    transaction_type_enum.create(op.get_bind(), checkfirst=True)
    transaction_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("api_key_hash", sa.String(length=256), nullable=False),
        sa.Column("webhook_secret", sa.String(length=128), nullable=False),
        sa.Column("allowed_ips", sa.String(length=512), nullable=True),
        sa.Column("plan", sa.String(length=50), nullable=False, server_default="starter"),
        sa.Column("webhook_url", sa.String(length=512), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=120), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=120), nullable=True),
        sa.Column("monthly_quota", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenants_id"), "tenants", ["id"], unique=False)
    op.create_unique_constraint("uq_tenants_name", "tenants", ["name"])

    op.create_table(
        "api_key_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("last_two", sa.String(length=4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tenant_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("month_start", sa.Date(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_request_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "month_start", name="uq_tenant_month"),
    )
    op.create_index(op.f("ix_tenant_usage_tenant_id"), "tenant_usage", ["tenant_id"], unique=False)

    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_reference", sa.String(length=120), nullable=False),
        sa.Column("network", network_enum, nullable=False),
        sa.Column("address", sa.String(length=256), nullable=False),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_reference", "network", name="uq_wallet_user_network"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=True),
        sa.Column("type", transaction_type_enum, nullable=False),
        sa.Column("network", network_enum, nullable=False),
        sa.Column("status", transaction_status_enum, nullable=False, server_default="pending"),
        sa.Column("amount_usdc", sa.Numeric(precision=38, scale=6), nullable=False),
        sa.Column("fee_usdc", sa.Numeric(precision=38, scale=6), nullable=True),
        sa.Column("tx_hash", sa.String(length=256), nullable=True),
        sa.Column("from_address", sa.String(length=256), nullable=True),
        sa.Column("to_address", sa.String(length=256), nullable=True),
        sa.Column("provider_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)
    op.create_index(op.f("ix_transactions_idempotency_key"), "transactions", ["idempotency_key"], unique=False)
    op.create_index(op.f("ix_transactions_tenant_id"), "transactions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_transactions_tx_hash"), "transactions", ["tx_hash"], unique=False)

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=512), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_webhook_deliveries_tenant_id"), "webhook_deliveries", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_webhook_deliveries_tenant_id"), table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")

    op.drop_index(op.f("ix_transactions_tx_hash"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_tenant_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_idempotency_key"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_id"), table_name="transactions")
    op.drop_table("transactions")

    op.drop_table("wallets")

    op.drop_index(op.f("ix_tenant_usage_tenant_id"), table_name="tenant_usage")
    op.drop_table("tenant_usage")

    op.drop_table("api_key_audits")

    op.drop_constraint("uq_tenants_name", "tenants", type_="unique")
    op.drop_index(op.f("ix_tenants_id"), table_name="tenants")
    op.drop_table("tenants")

    transaction_status_enum.drop(op.get_bind(), checkfirst=True)
    transaction_type_enum.drop(op.get_bind(), checkfirst=True)
    network_enum.drop(op.get_bind(), checkfirst=True)
