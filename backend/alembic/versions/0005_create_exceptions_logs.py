"""创建异常记录与操作日志表

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exception_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False, server_default="other"),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("handler_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["handler_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_exceptions_package", "exception_records", ["package_id"])
    op.create_index("idx_exceptions_status", "exception_records", ["status"])
    op.create_index("idx_exceptions_type", "exception_records", ["type"])

    op.create_table(
        "operation_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("module", sa.String(length=30), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=True),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_logs_user_time", "operation_logs", ["user_id", "created_at"])
    op.create_index("idx_logs_module_time", "operation_logs", ["module", "created_at"])
    op.create_index("ix_operation_logs_module", "operation_logs", ["module"])


def downgrade() -> None:
    op.drop_index("ix_operation_logs_module", table_name="operation_logs")
    op.drop_index("idx_logs_module_time", table_name="operation_logs")
    op.drop_index("idx_logs_user_time", table_name="operation_logs")
    op.drop_table("operation_logs")

    op.drop_index("idx_exceptions_type", table_name="exception_records")
    op.drop_index("idx_exceptions_status", table_name="exception_records")
    op.drop_index("idx_exceptions_package", table_name="exception_records")
    op.drop_table("exception_records")
