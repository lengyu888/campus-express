from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.errors import ApiError
from app.core.response import ok
from app.db.session import get_db
from app.models.shelf import Shelf
from app.models.station import Station
from app.models.user import User
from app.schemas.station import (
    ShelfCreate, ShelfUpdate, StationCreate, StationStatus, StationUpdate,
    to_time,
)

router = APIRouter(tags=["驿站与货架"])


def fmt_time(value):
    return value.strftime("%H:%M") if value else None


def shelf_payload(shelf: Shelf) -> dict:
    occupancy = round(shelf.used_count / shelf.capacity, 4) if shelf.capacity else 0
    return {
        "id": shelf.id,
        "station_id": shelf.station_id,
        "code": shelf.code,
        "zone": shelf.zone,
        "capacity": shelf.capacity,
        "used_count": shelf.used_count,
        "occupancy": occupancy,
        "status": shelf.status,
    }


def station_payload(station: Station) -> dict:
    shelves = station.shelves or []
    capacity = sum(s.capacity for s in shelves)
    used = sum(s.used_count for s in shelves)
    return {
        "id": station.id,
        "code": station.code,
        "name": station.name,
        "address": station.address,
        "phone": station.phone,
        "open_time": fmt_time(station.open_time),
        "close_time": fmt_time(station.close_time),
        "capacity": capacity,
        "used_count": used,
        "shelf_count": len(shelves),
        "occupancy": round(used / capacity, 4) if capacity else 0,
        "manager_id": station.manager_id,
        "manager_name": station.manager.name if station.manager else None,
        "status": station.status,
        "created_at": station.created_at.isoformat() if station.created_at else None,
        "shelves": [shelf_payload(s) for s in shelves],
    }


def sync_capacity(db: Session, station: Station) -> None:
    total = db.scalar(
        select(func.sum(Shelf.capacity)).where(Shelf.station_id == station.id)
    ) or 0
    station.capacity = int(total)


def get_station_or_404(db: Session, station_id: int) -> Station:
    station = db.get(Station, station_id)
    if station is None:
        raise ApiError(10004, "驿站不存在", 404)
    return station


@router.get("/stations", summary="驿站列表")
def list_stations(
    request: Request,
    status: int | None = None,
    keyword: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Station)
    if status is not None:
        stmt = stmt.where(Station.status == status)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Station.name.like(like), Station.code.like(like)))
    stations = db.execute(stmt.order_by(Station.id.asc())).scalars().all()
    return ok(request, {"items": [station_payload(s) for s in stations], "total": len(stations)})


@router.post("/stations", summary="新增驿站")
def create_station(
    payload: StationCreate,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    exists = db.execute(select(Station.id).where(Station.code == payload.code)).scalar_one_or_none()
    if exists:
        raise ApiError(10005, "驿站编码已存在，请更换", 409)

    if payload.manager_id is not None:
        manager = db.get(User, payload.manager_id)
        if manager is None or manager.role not in ("staff", "admin"):
            raise ApiError(10001, "负责人必须是工作人员或管理员", 422)

    station = Station(
        code=payload.code,
        name=payload.name,
        address=payload.address,
        phone=payload.phone,
        open_time=to_time(payload.open_time),
        close_time=to_time(payload.close_time),
        manager_id=payload.manager_id,
        capacity=0,
        status=1,
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return ok(request, station_payload(station), "驿站创建成功", 201)


@router.get("/stations/{station_id}", summary="驿站详情")
def get_station(
    station_id: int,
    request: Request,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(request, station_payload(get_station_or_404(db, station_id)))


@router.put("/stations/{station_id}", summary="修改驿站")
def update_station(
    station_id: int,
    payload: StationUpdate,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    station = get_station_or_404(db, station_id)
    fields = payload.model_fields_set

    if "manager_id" in fields:
        if payload.manager_id is not None:
            manager = db.get(User, payload.manager_id)
            if manager is None or manager.role not in ("staff", "admin"):
                raise ApiError(10001, "负责人必须是工作人员或管理员", 422)
        station.manager_id = payload.manager_id

    if payload.name is not None:
        station.name = payload.name
    if payload.address is not None:
        station.address = payload.address
    if "phone" in fields:
        station.phone = payload.phone

    open_at = to_time(payload.open_time) if payload.open_time else station.open_time
    close_at = to_time(payload.close_time) if payload.close_time else station.close_time
    if open_at and close_at and close_at <= open_at:
        raise ApiError(10001, "营业结束时间必须晚于开始时间", 422)
    station.open_time = open_at
    station.close_time = close_at

    db.commit()
    db.refresh(station)
    return ok(request, station_payload(station), "驿站信息已更新")


@router.patch("/stations/{station_id}/status", summary="启用或停用驿站")
def update_station_status(
    station_id: int,
    payload: StationStatus,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    station = get_station_or_404(db, station_id)
    station.status = payload.status
    db.commit()
    db.refresh(station)
    return ok(request, station_payload(station), "驿站状态已更新")


@router.get("/stations/{station_id}/shelves", summary="货架列表")
def list_shelves(
    station_id: int,
    request: Request,
    _: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    station = get_station_or_404(db, station_id)
    shelves = sorted(station.shelves, key=lambda s: s.id)
    return ok(request, {"items": [shelf_payload(s) for s in shelves],
                        "station": station_payload(station)})


@router.post("/stations/{station_id}/shelves", summary="新增货架")
def create_shelf(
    station_id: int,
    payload: ShelfCreate,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    station = get_station_or_404(db, station_id)

    exists = db.execute(
        select(Shelf.id).where(Shelf.station_id == station_id, Shelf.code == payload.code)
    ).scalar_one_or_none()
    if exists:
        raise ApiError(10005, "该驿站下货架编号已存在", 409)

    shelf = Shelf(
        station_id=station_id,
        code=payload.code,
        zone=payload.zone,
        capacity=payload.capacity,
        used_count=0,
        status=1,
    )
    db.add(shelf)
    db.flush()
    sync_capacity(db, station)
    db.commit()
    db.refresh(shelf)
    return ok(request, shelf_payload(shelf), "货架创建成功", 201)


@router.put("/shelves/{shelf_id}", summary="修改货架")
def update_shelf(
    shelf_id: int,
    payload: ShelfUpdate,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    shelf = db.get(Shelf, shelf_id)
    if shelf is None:
        raise ApiError(10004, "货架不存在", 404)

    if payload.code is not None and payload.code != shelf.code:
        exists = db.execute(
            select(Shelf.id).where(
                Shelf.station_id == shelf.station_id,
                Shelf.code == payload.code,
                Shelf.id != shelf.id,
            )
        ).scalar_one_or_none()
        if exists:
            raise ApiError(10005, "该驿站下货架编号已存在", 409)
        shelf.code = payload.code

    if payload.capacity is not None:
        if payload.capacity < shelf.used_count:
            raise ApiError(10005, "容量不能小于当前已用格口数", 409)
        shelf.capacity = payload.capacity

    if "zone" in payload.model_fields_set:
        shelf.zone = payload.zone
    if payload.status is not None:
        if payload.status == 0 and shelf.used_count > 0:
            raise ApiError(10005, "货架仍有包裹，不能停用", 409)
        shelf.status = payload.status

    station = get_station_or_404(db, shelf.station_id)
    sync_capacity(db, station)
    db.commit()
    db.refresh(shelf)
    return ok(request, shelf_payload(shelf), "货架信息已更新")


@router.delete("/shelves/{shelf_id}", summary="删除货架")
def delete_shelf(
    shelf_id: int,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    shelf = db.get(Shelf, shelf_id)
    if shelf is None:
        raise ApiError(10004, "货架不存在", 404)
    if shelf.used_count > 0:
        raise ApiError(10005, "该货架仍有包裹，无法删除", 409)

    station = get_station_or_404(db, shelf.station_id)
    db.delete(shelf)
    db.flush()
    sync_capacity(db, station)
    db.commit()
    return ok(request, None, "货架已删除")
