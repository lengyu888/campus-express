from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import require_roles
from app.core.response import ok
from app.db.session import get_db
from app.models.package import Package
from app.models.shelf import Shelf
from app.models.shipment import ShipmentOrder
from app.models.station import Station
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["统计报表"])


def start_of_today() -> datetime:
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def _int(value) -> int:
    return int(value or 0)


@router.get("/overview", summary="总览指标")
def overview(
    request: Request,
    station_id: int | None = None,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    """包裹、寄件、格口与用户指标合并为 4 条聚合查询，避免逐项 count。"""
    today = start_of_today()
    cutoff = datetime.now() - timedelta(days=settings.OVERDUE_THRESHOLD_DAYS)
    station_filter = [Package.station_id == station_id] if station_id is not None else []

    pkg_row = db.execute(
        select(
            func.sum(case((and_(Package.status == "in_stock", Package.stored_at > cutoff), 1), else_=0)),
            func.sum(case((and_(Package.status == "in_stock", Package.stored_at <= cutoff), 1), else_=0)),
            func.sum(case((Package.stored_at >= today, 1), else_=0)),
            func.sum(case((and_(Package.picked_at.is_not(None), Package.picked_at >= today), 1), else_=0)),
            func.sum(case((Package.status == "returned", 1), else_=0)),
            func.sum(case((Package.status == "exception", 1), else_=0)),
            func.count(),
        )
        .select_from(Package)
        .where(*station_filter)
    ).one()
    in_stock, overdue, today_inbound, today_picked, returned, exception, packages_total = (
        _int(v) for v in pkg_row
    )

    ship_filter = (
        [ShipmentOrder.station_id == station_id] if station_id is not None else []
    )
    ship_row = db.execute(
        select(
            func.sum(case((ShipmentOrder.status == "pending", 1), else_=0)),
            func.sum(case((ShipmentOrder.created_at >= today, 1), else_=0)),
            func.count(),
        )
        .select_from(ShipmentOrder)
        .where(*ship_filter)
    ).one()
    shipments_pending, shipments_today, shipments_total = (_int(v) for v in ship_row)

    shelf_row = db.execute(
        select(
            func.coalesce(func.sum(Shelf.used_count), 0),
            func.coalesce(func.sum(Shelf.capacity), 0),
        ).where(*([Shelf.station_id == station_id] if station_id is not None else []))
    ).one()
    used, capacity = _int(shelf_row[0]), _int(shelf_row[1])

    counters = db.execute(
        select(
            select(func.count()).select_from(User).scalar_subquery(),
            select(func.count()).select_from(Station).scalar_subquery(),
        )
    ).one()

    return ok(
        request,
        {
            "in_stock": in_stock,
            "overdue": overdue,
            "today_inbound": today_inbound,
            "today_picked": today_picked,
            "returned": returned,
            "exception": exception,
            "packages_total": packages_total,
            "overdue_rate": round(overdue / (in_stock + overdue), 4) if (in_stock + overdue) else 0,
            "shipments_pending": shipments_pending,
            "shipments_total": shipments_total,
            "shipments_today": shipments_today,
            "users_total": _int(counters[0]),
            "stations_total": _int(counters[1]),
            "capacity": capacity,
            "used": used,
            "occupancy": round(used / capacity, 4) if capacity else 0,
        },
    )


@router.get("/packages/trend", summary="收发量趋势")
def package_trend(
    request: Request,
    days: int = Query(7, ge=3, le=30),
    station_id: int | None = None,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    today = start_of_today()
    start = today - timedelta(days=days - 1)

    inbound_stmt = (
        select(func.date(Package.stored_at).label("d"), func.count())
        .where(Package.stored_at >= start)
        .group_by("d")
    )
    picked_stmt = (
        select(func.date(Package.picked_at).label("d"), func.count())
        .where(Package.picked_at.is_not(None), Package.picked_at >= start)
        .group_by("d")
    )
    if station_id is not None:
        inbound_stmt = inbound_stmt.where(Package.station_id == station_id)
        picked_stmt = picked_stmt.where(Package.station_id == station_id)

    inbound = {str(row[0]): int(row[1]) for row in db.execute(inbound_stmt).all()}
    picked = {str(row[0]): int(row[1]) for row in db.execute(picked_stmt).all()}

    series = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).date()
        key = day.isoformat()
        series.append(
            {"date": key, "label": f"{day.month}/{day.day}",
             "inbound": inbound.get(key, 0), "picked": picked.get(key, 0)}
        )

    return ok(
        request,
        {
            "days": days,
            "items": series,
            "inbound_total": sum(i["inbound"] for i in series),
            "picked_total": sum(i["picked"] for i in series),
        },
    )


@router.get("/stations/workload", summary="驿站工作量")
def station_workload(
    request: Request,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    """一次分组查询拿到全部驿站统计，再与驿站档案合并。"""
    cutoff = datetime.now() - timedelta(days=settings.OVERDUE_THRESHOLD_DAYS)
    rows = db.execute(
        select(
            Package.station_id,
            func.sum(case((and_(Package.status == "in_stock", Package.stored_at > cutoff), 1), else_=0)),
            func.sum(case((and_(Package.status == "in_stock", Package.stored_at <= cutoff), 1), else_=0)),
            func.sum(case((Package.status == "picked", 1), else_=0)),
            func.count(),
        ).group_by(Package.station_id)
    ).all()
    stats = {
        row[0]: (_int(row[1]), _int(row[2]), _int(row[3]), _int(row[4])) for row in rows
    }

    stations = db.execute(select(Station).order_by(Station.id.asc())).scalars().all()
    items = []
    for station in stations:
        in_stock, overdue, picked, total = stats.get(station.id, (0, 0, 0, 0))
        capacity = sum(s.capacity for s in station.shelves)
        used = sum(s.used_count for s in station.shelves)
        items.append(
            {
                "station_id": station.id,
                "name": station.name,
                "code": station.code,
                "status": station.status,
                "in_stock": in_stock,
                "overdue": overdue,
                "picked": picked,
                "total": total,
                "capacity": capacity,
                "used": used,
                "occupancy": round(used / capacity, 4) if capacity else 0,
            }
        )

    return ok(request, {"items": items})


@router.get("/overdue", summary="超期分析")
def overdue_stats(
    request: Request,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now() - timedelta(days=settings.OVERDUE_THRESHOLD_DAYS)
    rows = (
        db.execute(
            select(Package)
            .where(Package.status == "in_stock", Package.stored_at <= cutoff)
            .order_by(Package.stored_at.asc())
        )
        .scalars()
        .all()
    )

    now = datetime.now()
    buckets = [{"label": "1 天", "count": 0}, {"label": "2 天", "count": 0},
               {"label": "3-5 天", "count": 0}, {"label": "5 天以上", "count": 0}]
    items = []
    for pkg in rows:
        days = max(1, (now - pkg.stored_at).days - settings.OVERDUE_THRESHOLD_DAYS)
        if days <= 1:
            buckets[0]["count"] += 1
        elif days == 2:
            buckets[1]["count"] += 1
        elif days <= 5:
            buckets[2]["count"] += 1
        else:
            buckets[3]["count"] += 1
        items.append(
            {
                "id": pkg.id,
                "tracking_no": pkg.tracking_no,
                "recipient_name": pkg.recipient_name,
                "recipient_phone": pkg.recipient_phone,
                "station_name": pkg.station.name if pkg.station else None,
                "shelf_code": pkg.shelf.code if pkg.shelf else None,
                "stored_at": pkg.stored_at.isoformat() if pkg.stored_at else None,
                "overdue_days": days,
            }
        )

    total_in_stock = _int(
        db.scalar(
            select(func.count()).select_from(Package).where(
                Package.status == "in_stock", Package.stored_at > cutoff
            )
        )
    )
    overdue_total = len(items)
    return ok(
        request,
        {
            "overdue": overdue_total,
            "in_stock": total_in_stock,
            "overdue_rate": round(overdue_total / (overdue_total + total_in_stock), 4)
            if (overdue_total + total_in_stock) else 0,
            "buckets": buckets,
            "items": items[:10],
        },
    )
