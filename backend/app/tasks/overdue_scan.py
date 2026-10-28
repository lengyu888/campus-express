"""超期包裹扫描：给超过阈值的在库包裹推送提醒。

用法：
    python -m app.tasks.overdue_scan --dry-run
    python -m app.tasks.overdue_scan --cooldown-hours 24

建议由 cron / 计划任务每天执行一次，例如：
    0 9 * * *  cd /app && python -m app.tasks.overdue_scan
"""
import argparse
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.package import Package
from app.services.notify import push


def scan(cooldown_hours: int = 24, dry_run: bool = False) -> int:
    now = datetime.now()
    cutoff = now - timedelta(days=settings.OVERDUE_THRESHOLD_DAYS)
    cooldown_at = now - timedelta(hours=cooldown_hours)

    db = SessionLocal()
    try:
        packages = db.execute(
            select(Package).where(
                Package.status == "in_stock",
                Package.stored_at <= cutoff,
                Package.recipient_id.is_not(None),
            )
        ).scalars().all()

        sent = 0
        for pkg in packages:
            recent = db.scalar(
                select(Notification.id).where(
                    Notification.type == "overdue",
                    Notification.package_id == pkg.id,
                    Notification.created_at >= cooldown_at,
                )
            )
            if recent:
                continue

            days = max(1, (now - pkg.stored_at).days - settings.OVERDUE_THRESHOLD_DAYS)
            station = pkg.station.name if pkg.station else "驿站"
            print(f"[overdue] {pkg.tracking_no} 超期 {days} 天 → 用户 {pkg.recipient_id}")
            if not dry_run:
                push(
                    db,
                    pkg.recipient_id,
                    "overdue",
                    "包裹超期提醒",
                    f"您的包裹 {pkg.tracking_no} 已在 {station} 存放 {days} 天，"
                    f"请尽快凭取件码领取，超期过久将退回发件方。",
                    package_id=pkg.id,
                )
            sent += 1

        if not dry_run:
            db.commit()
        return sent
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描超期包裹并推送提醒")
    parser.add_argument("--cooldown-hours", type=int, default=24, help="同一包裹提醒间隔，默认 24 小时")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写通知")
    args = parser.parse_args()

    count = scan(args.cooldown_hours, args.dry_run)
    suffix = "（dry-run，未写入）" if args.dry_run else ""
    print(f"本次处理超期包裹 {count} 件{suffix}")


if __name__ == "__main__":
    main()
