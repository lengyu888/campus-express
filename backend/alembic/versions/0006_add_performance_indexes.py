"""补充高频查询的组合索引

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-28
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 包裹列表 / 超期统计：按状态 + 入库时间过滤
    op.create_index("ix_packages_status_stored", "packages", ["status", "stored_at"])
    # 操作日志：按时间倒序分页与清理
    op.create_index("ix_logs_created", "operation_logs", ["created_at"])
    # 异常列表：状态 + 时间排序
    op.create_index("ix_exceptions_status_created", "exception_records", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_exceptions_status_created", table_name="exception_records")
    op.drop_index("ix_logs_created", table_name="operation_logs")
    op.drop_index("ix_packages_status_stored", table_name="packages")
