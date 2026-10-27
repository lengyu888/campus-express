import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, require_roles
from app.core.errors import ApiError
from app.core.response import ok
from app.db.session import get_db
from app.models.package import Package
from app.models.pickup_record import PickupRecord
from app.models.shelf import Shelf
from app.models.station import Station
from app.models.user import User
from app.schemas.package import (
    ExceptionIn, PackageBatchCreate, PackageCreate, PackageItem, PickupVerify, ReturnIn,
    ShelfMove, to_iso,
)

router = APIRouter(tags=["快递与取件"])

STATUS_LABEL = {
    "in_stock": "在库",
    "picked": "已取件",
    "overdue": "超期",
    "returned": "已退回",
    "exception": "异常",
}
VERIFY_LABEL = {"code_phone": "取件码+手机号", "manual": "人工核验"}
EXCEPTION_LABEL = {
    "damaged": "包装破损",
    "wrong_station": "错分驿站",
    "no_phone": "联系方式缺失",
    "other": "其他异常",
}


# ---------------------------------------------------------------- 序列化
def effective_status(pkg: Package) -> tuple[str, int, int]:
    """返回（展示状态、超期天数、在库天数）。在库包裹按存放时长实时判定超期。"""
    days = max(0, (datetime.now() - pkg.stored_at).days)
    if pkg.status != "in_stock":
        return pkg.status, pkg.overdue_days, days

    cutoff = datetime.now() - timedelta(days=settings.OVERDUE_THRESHOLD_DAYS)
    if pkg.stored_at <= cutoff:
        return "overdue", max(1, days - settings.OVERDUE_THRESHOLD_DAYS), days
    return "in_stock", 0, days


def mask_phone(phone: str) -> str:
    return f"{phone[:3]}****{phone[-4:]}" if len(phone) == 11 else phone


def package_payload(pkg: Package, viewer: User, detail: bool = False) -> dict:
    status, overdue_days, days_in_stock = effective_status(pkg)
    is_staff = viewer.role in ("staff", "admin")
    data = {
        "id": pkg.id,
        "tracking_no": pkg.tracking_no,
        "station_id": pkg.station_id,
        "station_name": pkg.station.name if pkg.station else None,
        "station_code": pkg.station.code if pkg.station else None,
        "shelf_id": pkg.shelf_id,
        "shelf_code": pkg.shelf.code if pkg.shelf else None,
        "shelf_zone": pkg.shelf.zone if pkg.shelf else None,
        "recipient_id": pkg.recipient_id,
        "recipient_name": pkg.recipient_name,
        "recipient_phone": pkg.recipient_phone if is_staff else mask_phone(pkg.recipient_phone),
        "phone_suffix": pkg.recipient_phone[-4:],
        "courier_company": pkg.courier_company,
        "package_type": pkg.package_type,
        "weight": float(pkg.weight) if pkg.weight is not None else None,
        "status": status,
        "status_label": STATUS_LABEL.get(status, status),
        "pickup_code": pkg.pickup_code if status in ("in_stock", "overdue") else None,
        "code_expire_at": to_iso(pkg.code_expire_at),
        "stored_at": to_iso(pkg.stored_at),
        "picked_at": to_iso(pkg.picked_at),
        "days_in_stock": days_in_stock if status in ("in_stock", "overdue") else 0,
        "overdue_days": overdue_days,
        "remark": pkg.remark,
        "created_by_name": pkg.operator.name if pkg.operator else None,
        "created_at": to_iso(pkg.created_at),
    }
    if detail:
        data["timeline"] = build_timeline(pkg, viewer)
    return data


def build_timeline(pkg: Package, viewer: User) -> list[dict]:
    items = [
        {
            "title": "包裹入库",
            "desc": (
                f"{pkg.station.name if pkg.station else '驿站'} · "
                f"{pkg.shelf.code if pkg.shelf else '格口已释放'}"
            ),
            "at": to_iso(pkg.stored_at),
            "type": "inbound",
            "operator": pkg.operator.name if pkg.operator else None,
        }
    ]

    record = pkg.__dict__.get("_pickup_record")
    if pkg.status == "picked" and pkg.picked_at:
        items.append(
            {
                "title": "取件出库",
                "desc": f"核验方式：{VERIFY_LABEL.get(record.verify_type if record else 'code_phone')}",
                "at": to_iso(pkg.picked_at),
                "type": "picked",
                "operator": record.operator.name if record else None,
            }
        )
    elif pkg.status == "returned":
        items.append(
            {
                "title": "登记退回",
                "desc": pkg.remark or "包裹已退回发件方",
                "at": to_iso(pkg.updated_at),
                "type": "returned",
                "operator": None,
            }
        )
    elif pkg.status == "exception":
        items.append(
            {
                "title": "登记异常",
                "desc": pkg.remark or "包裹状态异常，等待处理",
                "at": to_iso(pkg.updated_at),
                "type": "exception",
                "operator": None,
            }
        )
    return items


def pickup_record_payload(record: PickupRecord) -> dict:
    pkg = record.package
    return {
        "id": record.id,
        "package_id": record.package_id,
        "tracking_no": pkg.tracking_no if pkg else None,
        "recipient_name": pkg.recipient_name if pkg else None,
        "recipient_phone": pkg.recipient_phone if pkg else None,
        "station_name": pkg.station.name if pkg and pkg.station else None,
        "shelf_code": pkg.shelf.code if pkg and pkg.shelf else None,
        "pickup_code": record.pickup_code,
        "phone_suffix": record.phone_suffix,
        "verify_type": record.verify_type,
        "verify_label": VERIFY_LABEL.get(record.verify_type, record.verify_type),
        "picked_at": to_iso(record.picked_at),
        "operator_name": record.operator.name if record.operator else None,
        "remark": record.remark,
    }


# ---------------------------------------------------------------- 业务辅助
def get_package_or_404(db: Session, package_id: int) -> Package:
    pkg = db.get(Package, package_id)
    if pkg is None:
        raise ApiError(10004, "包裹不存在", 404)
    return pkg


def attach_pickup_record(db: Session, pkg: Package) -> None:
    record = db.execute(
        select(PickupRecord).where(PickupRecord.package_id == pkg.id)
    ).scalar_one_or_none()
    pkg.__dict__["_pickup_record"] = record


def pick_shelf(db: Session, station_id: int, shelf_id: int | None) -> Shelf:
    if shelf_id is not None:
        shelf = db.get(Shelf, shelf_id)
        if shelf is None or shelf.station_id != station_id:
            raise ApiError(10001, "货架不属于该驿站", 422)
        if shelf.status != 1:
            raise ApiError(10001, "该货架已停用，请更换", 422)
        if shelf.used_count >= shelf.capacity:
            raise ApiError(20005, "该货架格口已满，请更换货架", 409)
        return shelf

    shelf = db.execute(
        select(Shelf)
        .where(
            Shelf.station_id == station_id,
            Shelf.status == 1,
            Shelf.used_count < Shelf.capacity,
        )
        .order_by((Shelf.capacity - Shelf.used_count).desc())
        .limit(1)
    ).scalar_one_or_none()
    if shelf is None:
        raise ApiError(20005, "该驿站格口已满，请扩容或转投其他驿站", 409)
    return shelf


def gen_pickup_code(db: Session, station_id: int) -> str:
    for _ in range(5):
        code = f"{secrets.randbelow(1_000_000):06d}"
        exists = db.execute(
            select(Package.id).where(
                Package.station_id == station_id,
                Package.pickup_code == code,
            )
        ).scalar_one_or_none()
        if not exists:
            return code
    raise ApiError(50000, "取件码生成失败，请稍后重试", 500)


def validate_station(db: Session, station_id: int) -> Station:
    station = db.get(Station, station_id)
    if station is None:
        raise ApiError(10004, "驿站不存在", 404)
    if station.status != 1:
        raise ApiError(10005, "驿站已停用，暂不能入库", 409)
    return station


def do_inbound(db: Session, station: Station, item: PackageItem, operator: User) -> Package:
    exists = db.execute(
        select(Package).where(Package.tracking_no == item.tracking_no)
    ).scalar_one_or_none()
    if exists is not None:
        raise ApiError(
            20001,
            f"运单号已入库（{exists.stored_at:%Y-%m-%d %H:%M}）",
            409,
            {"package_id": exists.id, "stored_at": to_iso(exists.stored_at)},
        )

    recipient = db.execute(
        select(User).where(User.phone == item.recipient_phone)
    ).scalar_one_or_none()
    if recipient is not None and recipient.status != 1:
        recipient = None

    shelf = pick_shelf(db, station.id, item.shelf_id)
    now = datetime.now()
    pkg = Package(
        tracking_no=item.tracking_no,
        station_id=station.id,
        shelf_id=shelf.id,
        recipient_id=recipient.id if recipient else None,
        recipient_name=item.recipient_name or (recipient.name if recipient else None),
        recipient_phone=item.recipient_phone,
        courier_company=item.courier_company,
        package_type=item.package_type,
        weight=item.weight,
        status="in_stock",
        pickup_code=gen_pickup_code(db, station.id),
        code_expire_at=now + timedelta(days=settings.PICKUP_CODE_EXPIRE_DAYS),
        stored_at=now,
        overdue_days=0,
        remark=item.remark,
        created_by=operator.id,
    )
    db.add(pkg)
    db.execute(
        update(Shelf).where(Shelf.id == shelf.id).values(used_count=Shelf.used_count + 1)
    )
    db.flush()
    return pkg


# ---------------------------------------------------------------- 查询
@router.get("/packages", summary="包裹列表")
def list_packages(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    station_id: int | None = None,
    status: str | None = None,
    package_type: str | None = None,
    keyword: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Package)
    if user.role == "student":
        stmt = stmt.where(
            or_(Package.recipient_id == user.id, Package.recipient_phone == user.phone)
        )

    if station_id is not None:
        stmt = stmt.where(Package.station_id == station_id)
    if package_type:
        stmt = stmt.where(Package.package_type == package_type)

    cutoff = datetime.now() - timedelta(days=settings.OVERDUE_THRESHOLD_DAYS)
    if status == "overdue":
        stmt = stmt.where(Package.status == "in_stock", Package.stored_at <= cutoff)
    elif status == "in_stock":
        stmt = stmt.where(Package.status == "in_stock", Package.stored_at > cutoff)
    elif status:
        stmt = stmt.where(Package.status == status)

    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                Package.tracking_no.like(like),
                Package.recipient_name.like(like),
                Package.recipient_phone.like(like),
                Package.pickup_code.like(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(
            stmt.order_by(Package.stored_at.desc(), Package.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return ok(
        request,
        {
            "items": [package_payload(p, user) for p in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/packages/summary", summary="包裹统计指标")
def packages_summary(
    request: Request,
    station_id: int | None = None,
    user: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff = datetime.now() - timedelta(days=settings.OVERDUE_THRESHOLD_DAYS)

    def count(*conditions) -> int:
        stmt = select(func.count()).select_from(Package).where(*conditions)
        if station_id is not None:
            stmt = stmt.where(Package.station_id == station_id)
        return int(db.scalar(stmt) or 0)

    in_stock = count(Package.status == "in_stock", Package.stored_at > cutoff)
    overdue = count(Package.status == "in_stock", Package.stored_at <= cutoff)
    data = {
        "in_stock": in_stock,
        "overdue": overdue,
        "today_inbound": count(Package.stored_at >= today),
        "today_picked": count(Package.picked_at >= today),
        "picked": count(Package.status == "picked"),
        "returned": count(Package.status == "returned"),
        "exception": count(Package.status == "exception"),
        "total": count(),
    }
    return ok(request, data)


@router.get("/packages/by-code/{code}", summary="按取件码查询在库包裹")
def get_package_by_code(
    code: str,
    request: Request,
    station_id: int | None = None,
    user: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    stmt = select(Package).where(Package.pickup_code == code, Package.status == "in_stock")
    if station_id is not None:
        stmt = stmt.where(Package.station_id == station_id)
    pkg = db.execute(stmt.order_by(Package.stored_at.desc()).limit(1)).scalar_one_or_none()
    if pkg is None:
        raise ApiError(20002, "取件码不存在或包裹已出库", 404)
    return ok(request, package_payload(pkg, user))


@router.get("/packages/track/{tracking_no}", summary="按运单号查询包裹")
def track_package(
    tracking_no: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pkg = db.execute(
        select(Package).where(Package.tracking_no == tracking_no.strip().upper())
    ).scalar_one_or_none()
    if pkg is None:
        raise ApiError(10004, "未查询到该运单号", 404)
    if user.role == "student" and pkg.recipient_phone != user.phone:
        raise ApiError(10003, "无权查看该包裹", 403)
    attach_pickup_record(db, pkg)
    return ok(request, package_payload(pkg, user, detail=True))


@router.get("/packages/{package_id}", summary="包裹详情")
def get_package(
    package_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pkg = get_package_or_404(db, package_id)
    if user.role == "student" and pkg.recipient_phone != user.phone:
        raise ApiError(10003, "无权查看该包裹", 403)
    attach_pickup_record(db, pkg)
    return ok(request, package_payload(pkg, user, detail=True))


# ---------------------------------------------------------------- 入库
@router.post("/packages", summary="单件入库")
def create_package(
    payload: PackageCreate,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    station = validate_station(db, payload.station_id)
    try:
        item = PackageItem(**payload.model_dump(exclude={"station_id"}))
        pkg = do_inbound(db, station, item, operator)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(20001, "运单号已入库，请勿重复登记", 409) from exc
    db.refresh(pkg)
    return ok(request, package_payload(pkg, operator), "入库成功，取件码已生成", 201)


@router.post("/packages/batch", summary="批量入库")
def create_packages_batch(
    payload: PackageBatchCreate,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    station = validate_station(db, payload.station_id)
    results = []
    success = 0

    for index, item in enumerate(payload.items, start=1):
        try:
            with db.begin_nested():
                pkg = do_inbound(db, station, item, operator)
            success += 1
            results.append(
                {
                    "index": index,
                    "tracking_no": item.tracking_no,
                    "success": True,
                    "package_id": pkg.id,
                    "pickup_code": pkg.pickup_code,
                }
            )
        except ApiError as exc:
            results.append(
                {
                    "index": index,
                    "tracking_no": item.tracking_no,
                    "success": False,
                    "code": exc.code,
                    "message": exc.message,
                }
            )
        except IntegrityError:
            results.append(
                {
                    "index": index,
                    "tracking_no": item.tracking_no,
                    "success": False,
                    "code": 20001,
                    "message": "运单号已入库",
                }
            )
    db.commit()
    return ok(
        request,
        {"total": len(payload.items), "success": success, "failed": len(payload.items) - success,
         "items": results},
        f"批量入库完成：成功 {success} 件，失败 {len(payload.items) - success} 件",
    )


# ---------------------------------------------------------------- 在库操作
@router.post("/packages/{package_id}/shelf", summary="调整货架格口")
def move_shelf(
    package_id: int,
    payload: ShelfMove,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    pkg = get_package_or_404(db, package_id)
    if pkg.status not in ("in_stock", "overdue"):
        raise ApiError(20004, "仅在库包裹可以调整格口", 409)
    if payload.shelf_id == pkg.shelf_id:
        return ok(request, package_payload(pkg, operator), "货架未变更")

    old_shelf_id = pkg.shelf_id
    shelf = pick_shelf(db, pkg.station_id, payload.shelf_id)
    if old_shelf_id:
        db.execute(
            update(Shelf)
            .where(Shelf.id == old_shelf_id)
            .values(used_count=func.greatest(Shelf.used_count - 1, 0))
        )
    db.execute(update(Shelf).where(Shelf.id == shelf.id).values(used_count=Shelf.used_count + 1))
    pkg.shelf_id = shelf.id
    db.commit()
    db.refresh(pkg)
    return ok(request, package_payload(pkg, operator), f"已调整至 {shelf.code} 货架")


@router.post("/packages/{package_id}/pickup", summary="取件核验并出库")
def pickup_package(
    package_id: int,
    payload: PickupVerify,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    pkg = db.get(Package, package_id, with_for_update=True)
    if pkg is None:
        raise ApiError(10004, "包裹不存在", 404)
    if pkg.status not in ("in_stock", "overdue"):
        raise ApiError(20004, f"该包裹当前为{STATUS_LABEL.get(pkg.status, pkg.status)}状态，不能出库", 409)

    now = datetime.now()
    if payload.verify_type == "code_phone":
        if pkg.pickup_code != payload.pickup_code:
            raise ApiError(20002, "取件码不正确，请核对后重试", 400)
        if pkg.code_expire_at and pkg.code_expire_at < now:
            raise ApiError(20002, "取件码已过期，请改用人工核验", 400)

    if pkg.recipient_phone[-4:] != payload.phone_suffix:
        raise ApiError(20003, "手机号后四位与收件人不一致", 400)

    _, overdue_days, _ = effective_status(pkg)
    pkg.status = "picked"
    pkg.picked_at = now
    pkg.overdue_days = overdue_days

    record = PickupRecord(
        package_id=pkg.id,
        operator_id=operator.id,
        pickup_code=payload.pickup_code or pkg.pickup_code or "------",
        phone_suffix=payload.phone_suffix,
        verify_type=payload.verify_type,
        picked_at=now,
        remark=payload.remark,
    )
    db.add(record)

    old_shelf_id = pkg.shelf_id
    pkg.shelf_id = None
    pkg.pickup_code = None
    pkg.code_expire_at = None
    if old_shelf_id:
        db.execute(
            update(Shelf)
            .where(Shelf.id == old_shelf_id)
            .values(used_count=func.greatest(Shelf.used_count - 1, 0))
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(20004, "该包裹已被出库，请勿重复操作", 409) from exc

    db.refresh(pkg)
    return ok(
        request,
        {"package": package_payload(pkg, operator), "record": pickup_record_payload(record)},
        f"出库成功，格口 {pkg.station.name if pkg.station else ''} 已释放",
    )


@router.post("/packages/{package_id}/return", summary="登记退回")
def return_package(
    package_id: int,
    payload: ReturnIn,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    pkg = db.get(Package, package_id, with_for_update=True)
    if pkg is None:
        raise ApiError(10004, "包裹不存在", 404)
    if pkg.status not in ("in_stock", "overdue"):
        raise ApiError(20004, "仅在库包裹可以登记退回", 409)

    old_shelf_id = pkg.shelf_id
    pkg.status = "returned"
    pkg.shelf_id = None
    pkg.pickup_code = None
    pkg.code_expire_at = None
    pkg.remark = payload.reason
    if old_shelf_id:
        db.execute(
            update(Shelf)
            .where(Shelf.id == old_shelf_id)
            .values(used_count=func.greatest(Shelf.used_count - 1, 0))
        )
    db.commit()
    db.refresh(pkg)
    return ok(request, package_payload(pkg, operator), "已登记退回，格口已释放")


@router.post("/packages/{package_id}/exception", summary="登记异常件")
def mark_exception(
    package_id: int,
    payload: ExceptionIn,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    pkg = get_package_or_404(db, package_id)
    if pkg.status not in ("in_stock", "overdue"):
        raise ApiError(20004, "仅在库包裹可以登记异常", 409)

    pkg.status = "exception"
    pkg.remark = f"{EXCEPTION_LABEL[payload.exception_type]}：{payload.remark or '待处理'}"
    db.commit()
    db.refresh(pkg)
    return ok(request, package_payload(pkg, operator), "异常已登记")


# ---------------------------------------------------------------- 取件记录
@router.get("/pickup-records", summary="取件记录")
def list_pickup_records(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    station_id: int | None = None,
    keyword: str | None = None,
    today_only: bool = False,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    stmt = select(PickupRecord).join(Package, Package.id == PickupRecord.package_id)
    if station_id is not None:
        stmt = stmt.where(Package.station_id == station_id)
    if today_only:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = stmt.where(PickupRecord.picked_at >= today)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                Package.tracking_no.like(like),
                Package.recipient_name.like(like),
                Package.recipient_phone.like(like),
                PickupRecord.pickup_code.like(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(
            stmt.order_by(PickupRecord.picked_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return ok(
        request,
        {
            "items": [pickup_record_payload(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )
