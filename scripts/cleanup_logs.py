# -*- coding: utf-8 -*-
"""清理历史操作日志（默认保留 90 天）。

用法：
    python scripts/cleanup_logs.py --days 90 --dry-run
    python scripts/cleanup_logs.py --days 90

注意：脚本读取 backend/.env 或环境变量 DATABASE_URL，
本地开发模式（MySQL 暴露 3306）可直接执行；全栈 Docker 模式需在 backend 容器内运行：
    docker compose exec backend python /app/../scripts/cleanup_logs.py --days 90
（容器内未挂载 scripts 时，可直接执行 SQL 清理，见 docs/部署说明.md）
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import delete, func, select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.notification import Notification  # noqa: E402
from app.models.operation_log import OperationLog  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="清理历史操作日志与已读通知")
    parser.add_argument("--days", type=int, default=90, help="保留天数，默认 90")
    parser.add_argument("--dry-run", action="store_true", help="只统计不删除")
    parser.add_argument("--with-notifications", action="store_true", help="同时清理已读通知")
    args = parser.parse_args()

    cutoff = datetime.now() - timedelta(days=args.days)
    db = SessionLocal()
    try:
        log_count = db.scalar(
            select(func.count()).select_from(OperationLog).where(OperationLog.created_at < cutoff)
        ) or 0
        print(f"操作日志早于 {cutoff:%Y-%m-%d %H:%M} 的记录：{log_count} 条")

        notify_count = 0
        if args.with_notifications:
            notify_count = db.scalar(
                select(func.count()).select_from(Notification).where(
                    Notification.is_read == 1, Notification.created_at < cutoff
                )
            ) or 0
            print(f"已读通知早于该时间的记录：{notify_count} 条")

        if args.dry_run:
            print("dry-run：未执行删除")
            return

        if log_count:
            db.execute(delete(OperationLog).where(OperationLog.created_at < cutoff))
        if notify_count:
            db.execute(
                delete(Notification).where(
                    Notification.is_read == 1, Notification.created_at < cutoff
                )
            )
        db.commit()
        print(f"已删除操作日志 {log_count} 条、已读通知 {notify_count} 条")
    finally:
        db.close()


if __name__ == "__main__":
    main()
