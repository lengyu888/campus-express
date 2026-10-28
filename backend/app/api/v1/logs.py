from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ok
from app.db.session import get_db
from app.models.operation_log import OperationLog
from app.models.user import User
from app.services.audit import ACTION_LABELS, MODULE_LABELS

router = APIRouter(prefix="/logs", tags=["操作日志"])


@router.get("", summary="操作日志列表")
def list_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    module: str | None = None,
    action: str | None = None,
    keyword: str | None = None,
    start: date | None = None,
    end: date | None = None,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    stmt = (
        select(OperationLog, User)
        .outerjoin(User, User.id == OperationLog.user_id)
    )
    if module:
        stmt = stmt.where(OperationLog.module == module)
    if action:
        stmt = stmt.where(OperationLog.action == action)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(User.name.like(like), User.student_no.like(like)))
    if start:
        stmt = stmt.where(OperationLog.created_at >= datetime.combine(start, datetime.min.time()))
    if end:
        stmt = stmt.where(
            OperationLog.created_at < datetime.combine(end + timedelta(days=1), datetime.min.time())
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(OperationLog.created_at.desc(), OperationLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = []
    for log, user in rows:
        items.append(
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": user.name if user else "系统",
                "user_role": user.role if user else None,
                "module": log.module,
                "module_label": MODULE_LABELS.get(log.module, log.module),
                "action": log.action,
                "action_label": ACTION_LABELS.get(log.action, log.action),
                "target_type": log.target_type,
                "target_id": log.target_id,
                "detail": log.detail,
                "ip": log.ip,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    return ok(request, {"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/summary", summary="操作日志统计")
def log_summary(
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total = int(db.scalar(select(func.count()).select_from(OperationLog)) or 0)
    today_count = int(
        db.scalar(
            select(func.count()).select_from(OperationLog).where(OperationLog.created_at >= today)
        ) or 0
    )
    rows = db.execute(
        select(OperationLog.module, func.count())
        .group_by(OperationLog.module)
        .order_by(func.count().desc())
    ).all()
    modules = [
        {"module": m, "label": MODULE_LABELS.get(m, m), "count": int(c)} for m, c in rows
    ]
    return ok(request, {"total": total, "today": today_count, "modules": modules})
