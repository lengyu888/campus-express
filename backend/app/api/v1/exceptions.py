from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.errors import ApiError
from app.core.response import ok
from app.db.session import get_db
from app.models.exception_record import ExceptionRecord
from app.models.package import Package
from app.models.shelf import Shelf
from app.models.user import User
from app.schemas.exception import ExceptionHandle
from app.services.notify import push

router = APIRouter(prefix="/exceptions", tags=["异常件"])

TYPE_LABEL = {
    "damaged": "包装破损",
    "lost": "包裹丢失",
    "wrong_station": "错分驿站",
    "returned": "异常退回",
    "other": "其他异常",
}
STATUS_LABEL = {"open": "待处理", "processing": "处理中", "resolved": "已解决"}
ACTION_LABEL = {"keep": "保持异常", "restock": "重新入库", "returned": "退回发件方"}


def payload(item: ExceptionRecord) -> dict:
    pkg = item.package
    return {
        "id": item.id,
        "package_id": item.package_id,
        "tracking_no": pkg.tracking_no if pkg else None,
        "recipient_name": pkg.recipient_name if pkg else None,
        "recipient_phone": pkg.recipient_phone if pkg else None,
        "station_id": pkg.station_id if pkg else None,
        "station_name": pkg.station.name if pkg and pkg.station else None,
        "shelf_code": pkg.shelf.code if pkg and pkg.shelf else None,
        "package_status": pkg.status if pkg else None,
        "type": item.type,
        "type_label": TYPE_LABEL.get(item.type, item.type),
        "description": item.description,
        "status": item.status,
        "status_label": STATUS_LABEL.get(item.status, item.status),
        "handler_name": item.handler.name if item.handler else None,
        "creator_name": item.creator.name if item.creator else None,
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("", summary="异常件列表")
def list_exceptions(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    type: str | None = None,
    station_id: int | None = None,
    keyword: str | None = None,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    stmt = select(ExceptionRecord).join(Package, Package.id == ExceptionRecord.package_id)
    if status:
        stmt = stmt.where(ExceptionRecord.status == status)
    if type:
        stmt = stmt.where(ExceptionRecord.type == type)
    if station_id is not None:
        stmt = stmt.where(Package.station_id == station_id)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                Package.tracking_no.like(like),
                Package.recipient_name.like(like),
                Package.recipient_phone.like(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(
            stmt.order_by(ExceptionRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return ok(
        request,
        {"items": [payload(r) for r in rows], "total": total, "page": page, "page_size": page_size},
    )


@router.get("/summary", summary="异常件统计")
def exception_summary(
    request: Request,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    def count(status: str) -> int:
        return int(
            db.scalar(
                select(func.count()).select_from(ExceptionRecord).where(
                    ExceptionRecord.status == status
                )
            ) or 0
        )

    return ok(
        request,
        {"open": count("open"), "processing": count("processing"), "resolved": count("resolved"),
         "total": int(db.scalar(select(func.count()).select_from(ExceptionRecord)) or 0)},
    )


@router.patch("/{exception_id}", summary="处理异常件")
def handle_exception(
    exception_id: int,
    body: ExceptionHandle,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    item = db.get(ExceptionRecord, exception_id)
    if item is None:
        raise ApiError(10004, "异常记录不存在", 404)
    if item.status == "resolved":
        raise ApiError(10005, "该异常已解决，不能重复处理", 409)

    if body.status == "processing" and item.status != "open":
        raise ApiError(10005, "当前状态不能转为处理中", 409)

    item.status = body.status
    item.handler_id = operator.id
    if body.remark:
        item.description = f"{item.description}\n处理记录：{body.remark}"

    message = f"异常已转入{STATUS_LABEL[body.status]}"
    if body.status == "resolved":
        item.resolved_at = datetime.now()
        pkg = item.package
        if pkg is None:
            raise ApiError(10004, "关联包裹不存在", 404)

        if body.package_action == "restock":
            if pkg.shelf_id is None:
                raise ApiError(10005, "包裹已释放格口，请先调整格口再重新入库", 409)
            pkg.status = "in_stock"
            pkg.remark = f"异常已处理（{ACTION_LABEL['restock']}）"
            message = "异常已解决，包裹重新入库"
        elif body.package_action == "returned":
            old_shelf = pkg.shelf_id
            pkg.status = "returned"
            pkg.shelf_id = None
            pkg.pickup_code = None
            pkg.code_expire_at = None
            pkg.remark = f"异常已处理（{ACTION_LABEL['returned']}）"
            if old_shelf:
                db.execute(
                    update(Shelf)
                    .where(Shelf.id == old_shelf)
                    .values(used_count=func.greatest(Shelf.used_count - 1, 0))
                )
            message = "异常已解决，包裹已退回发件方"
        else:
            message = "异常已解决，包裹保持异常状态"

        push(
            db, pkg.recipient_id, "system", "异常件已处理",
            f"包裹 {pkg.tracking_no} 的异常已处理：{TYPE_LABEL.get(item.type, item.type)}。"
            f"{body.remark or ''}",
            package_id=pkg.id,
        )

    db.commit()
    db.refresh(item)
    return ok(request, payload(item), message)
