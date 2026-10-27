from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import ApiError
from app.core.response import ok
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["通知"])

TYPE_LABEL = {
    "pickup": "取件",
    "overdue": "超期",
    "shipment": "寄件",
    "system": "系统",
}


def payload(item: Notification) -> dict:
    return {
        "id": item.id,
        "type": item.type,
        "type_label": TYPE_LABEL.get(item.type, item.type),
        "title": item.title,
        "content": item.content,
        "package_id": item.package_id,
        "order_id": item.order_id,
        "is_read": item.is_read,
        "sent_at": item.sent_at.isoformat() if item.sent_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("", summary="通知列表")
def list_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: str | None = None,
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Notification).where(Notification.user_id == user.id)
    if type:
        stmt = stmt.where(Notification.type == type)
    if unread_only:
        stmt = stmt.where(Notification.is_read == 0)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(
            stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    unread = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id, Notification.is_read == 0
        )
    ) or 0
    return ok(
        request,
        {"items": [payload(n) for n in rows], "total": total, "unread": int(unread)},
    )


@router.get("/unread-count", summary="未读数量")
def unread_count(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    unread = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id, Notification.is_read == 0
        )
    ) or 0
    return ok(request, {"unread": int(unread)})


@router.patch("/{notification_id}/read", summary="标记已读")
def mark_read(
    notification_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.get(Notification, notification_id)
    if item is None or item.user_id != user.id:
        raise ApiError(10004, "通知不存在", 404)
    item.is_read = 1
    db.commit()
    return ok(request, {"id": item.id, "is_read": 1}, "已标记为已读")


@router.post("/read-all", summary="全部标记已读")
def mark_all_read(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == 0)
        .values(is_read=1)
    )
    db.commit()
    return ok(request, {"updated": result.rowcount or 0}, "全部通知已标记为已读")
