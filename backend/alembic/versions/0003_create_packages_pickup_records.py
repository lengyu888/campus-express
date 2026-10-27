"""create packages and pickup records

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "packages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tracking_no", sa.String(length=40), nullable=False),
        sa.Column("station_id", sa.BigInteger(), nullable=False),
        sa.Column("shelf_id", sa.BigInteger(), nullable=True),
        sa.Column("recipient_id", sa.BigInteger(), nullable=True),
        sa.Column("recipient_name", sa.String(length=50), nullable=True),
        sa.Column("recipient_phone", sa.String(length=11), nullable=False),
        sa.Column("courier_company", sa.String(length=30), nullable=False),
        sa.Column("package_type", sa.String(length=16), nullable=False, server_default="normal"),
        sa.Column("weight", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="in_stock"),
        sa.Column("pickup_code", sa.String(length=6), nullable=True),
        sa.Column("code_expire_at", sa.DateTime(), nullable=True),
        sa.Column("stored_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("picked_at", sa.DateTime(), nullable=True),
        sa.Column("overdue_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shelf_id"], ["shelves.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tracking_no", name="uk_packages_tracking_no"),
        sa.UniqueConstraint("station_id", "pickup_code", name="uk_packages_station_code"),
    )
    op.create_index("ix_packages_station_id", "packages", ["station_id"])
    op.create_index("ix_packages_shelf_id", "packages", ["shelf_id"])
    op.create_index("ix_packages_recipient_id", "packages", ["recipient_id"])
    op.create_index("ix_packages_recipient_phone", "packages", ["recipient_phone"])
    op.create_index("ix_packages_status", "packages", ["status"])
    op.create_index("ix_packages_code_expire_at", "packages", ["code_expire_at"])

    op.create_table(
        "pickup_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.BigInteger(), nullable=False),
        sa.Column("operator_id", sa.BigInteger(), nullable=False),
        sa.Column("pickup_code", sa.String(length=6), nullable=False),
        sa.Column("phone_suffix", sa.String(length=4), nullable=False),
        sa.Column("verify_type", sa.String(length=16), nullable=False, server_default="code_phone"),
        sa.Column("picked_at", sa.DateTime(), nullable=False),
        sa.Column("remark", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("package_id", name="uk_pickup_records_package"),
    )
    op.create_index("ix_pickup_records_picked_at", "pickup_records", ["picked_at"])


def downgrade() -> None:
    op.drop_index("ix_pickup_records_picked_at", table_name="pickup_records")
    op.drop_table("pickup_records")
    op.drop_index("ix_packages_code_expire_at", table_name="packages")
    op.drop_index("ix_packages_status", table_name="packages")
    op.drop_index("ix_packages_recipient_phone", table_name="packages")
    op.drop_index("ix_packages_recipient_id", table_name="packages")
    op.drop_index("ix_packages_shelf_id", table_name="packages")
    op.drop_index("ix_packages_station_id", table_name="packages")
    op.drop_table("packages")
