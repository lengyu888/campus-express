from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.errors import ApiError
from app.core.response import ok
from app.db.session import get_db
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.shipment import AnnouncementIn

router = APIRouter(prefix="/announcements", tags=["公告"])


def payload(item: Announcement) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "publisher_name": item.publisher.name if item.publisher else None,
        "status": item.status,
        "publish_at": item.publish_at.isoformat() if item.publish_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("", summary="公告列表")
def list_announcements(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_offline: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Announcement)
    if not (include_offline and user.role == "admin"):
        stmt = stmt.where(Announcement.status == 1)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(
            stmt.order_by(Announcement.publish_at.desc(), Announcement.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return ok(request, {"items": [payload(a) for a in rows], "total": total})


@router.post("", summary="发布公告")
def create_announcement(
    body: AnnouncementIn,
    request: Request,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    item = Announcement(
        title=body.title,
        content=body.content,
        publisher_id=admin.id,
        status=body.status,
        publish_at=datetime.now() if body.status == 1 else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok(request, payload(item), "公告已发布", 201)


@router.put("/{announcement_id}", summary="修改公告")
def update_announcement(
    announcement_id: int,
    body: AnnouncementIn,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    item = db.get(Announcement, announcement_id)
    if item is None:
        raise ApiError(10004, "公告不存在", 404)

    item.title = body.title
    item.content = body.content
    if body.status != item.status:
        item.status = body.status
        item.publish_at = datetime.now() if body.status == 1 else item.publish_at
    elif item.status == 1 and item.publish_at is None:
        item.publish_at = datetime.now()
    db.commit()
    db.refresh(item)
    return ok(request, payload(item), "公告已更新")


@router.delete("/{announcement_id}", summary="下架公告")
def delete_announcement(
    announcement_id: int,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    item = db.get(Announcement, announcement_id)
    if item is None:
        raise ApiError(10004, "公告不存在", 404)
    item.status = 0
    db.commit()
    return ok(request, {"id": item.id, "status": 0}, "公告已下架")
