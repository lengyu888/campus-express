"""创建寄件、通知与公告表

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shipment_orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=False),
        sa.Column("station_id", sa.BigInteger(), nullable=False),
        sa.Column("receiver_name", sa.String(length=50), nullable=False),
        sa.Column("receiver_phone", sa.String(length=11), nullable=False),
        sa.Column("receiver_address", sa.String(length=200), nullable=False),
        sa.Column("courier_company", sa.String(length=30), nullable=True),
        sa.Column("item_name", sa.String(length=100), nullable=False),
        sa.Column("weight", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("freight", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no", name="uk_shipment_orders_no"),
    )
    op.create_index("ix_shipment_orders_sender", "shipment_orders", ["sender_id"])
    op.create_index("ix_shipment_orders_status", "shipment_orders", ["status"])
    op.create_index("ix_shipment_orders_station_status", "shipment_orders", ["station_id", "status"])

    op.create_table(
        "shipment_tracks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("node", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["shipment_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shipment_tracks_order", "shipment_tracks", ["order_id"])
    op.create_index("ix_shipment_tracks_time", "shipment_tracks", ["occurred_at"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False, server_default="system"),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.String(length=500), nullable=False),
        sa.Column("package_id", sa.BigInteger(), nullable=True),
        sa.Column("order_id", sa.BigInteger(), nullable=True),
        sa.Column("channel", sa.String(length=16), nullable=False, server_default="inapp"),
        sa.Column("is_read", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("idx_notifications_user_read", "notifications", ["user_id", "is_read"])

    op.create_table(
        "announcements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("publisher_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("publish_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["publisher_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_announcements_status", "announcements", ["status"])
    op.create_index("idx_announcements_status_time", "announcements", ["status", "publish_at"])


def downgrade() -> None:
    op.drop_index("idx_announcements_status_time", table_name="announcements")
    op.drop_index("ix_announcements_status", table_name="announcements")
    op.drop_table("announcements")

    op.drop_index("idx_notifications_user_read", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_shipment_tracks_time", table_name="shipment_tracks")
    op.drop_index("ix_shipment_tracks_order", table_name="shipment_tracks")
    op.drop_table("shipment_tracks")

    op.drop_index("ix_shipment_orders_station_status", table_name="shipment_orders")
    op.drop_index("ix_shipment_orders_status", table_name="shipment_orders")
    op.drop_index("ix_shipment_orders_sender", table_name="shipment_orders")
    op.drop_table("shipment_orders")
