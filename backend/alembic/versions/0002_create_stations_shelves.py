"""create stations and shelves

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("address", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=11), nullable=True),
        sa.Column("open_time", sa.Time(), nullable=True),
        sa.Column("close_time", sa.Time(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manager_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uk_stations_code"),
    )
    op.create_index("ix_stations_status", "stations", ["status"])

    op.create_table(
        "shelves",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("station_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("zone", sa.String(length=20), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("station_id", "code", name="uk_shelves_station_code"),
    )
    op.create_index("ix_shelves_station_id", "shelves", ["station_id"])


def downgrade() -> None:
    op.drop_index("ix_shelves_station_id", table_name="shelves")
    op.drop_table("shelves")
    op.drop_index("ix_stations_status", table_name="stations")
    op.drop_table("stations")
