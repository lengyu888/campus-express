import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.errors import ApiError
from app.core.response import ok
from app.db.session import get_db
from app.models.shipment import ShipmentOrder, ShipmentTrack
from app.models.station import Station
from app.models.user import User
from app.schemas.shipment import ShipmentAccept, ShipmentCreate, to_iso
from app.services.notify import calc_freight, push

router = APIRouter(tags=["寄件管理"])

STATUS_LABEL = {
    "pending": "待揽收",
    "accepted": "已揽收",
    "shipped": "已发出",
    "completed": "已完成",
    "cancelled": "已取消",
}


def shipment_payload(order: ShipmentOrder, detail: bool = False) -> dict:
    data = {
        "id": order.id,
        "order_no": order.order_no,
        "sender_id": order.sender_id,
        "sender_name": order.sender.name if order.sender else None,
        "sender_no": order.sender.student_no if order.sender else None,
        "sender_phone": order.sender.phone if order.sender else None,
        "station_id": order.station_id,
        "station_name": order.station.name if order.station else None,
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "receiver_address": order.receiver_address,
        "courier_company": order.courier_company,
        "item_name": order.item_name,
        "weight": float(order.weight) if order.weight is not None else None,
        "freight": float(order.freight) if order.freight is not None else None,
        "status": order.status,
        "status_label": STATUS_LABEL.get(order.status, order.status),
        "remark": order.remark,
        "created_at": to_iso(order.created_at),
        "updated_at": to_iso(order.updated_at),
    }
    tracks = list(order.tracks or [])
    data["track_count"] = len(tracks)
    data["latest_track"] = tracks[-1].node if tracks else None
    if detail:
        data["tracks"] = [
            {
                "id": t.id,
                "node": t.node,
                "status": t.status,
                "status_label": STATUS_LABEL.get(t.status, t.status),
                "description": t.description,
                "operator_name": t.operator.name if t.operator else None,
                "occurred_at": to_iso(t.occurred_at),
            }
            for t in tracks
        ]
    return data


def get_order_or_404(db: Session, order_id: int) -> ShipmentOrder:
    order = db.get(ShipmentOrder, order_id)
    if order is None:
        raise ApiError(10004, "寄件订单不存在", 404)
    return order


def ensure_visible(order: ShipmentOrder, user: User) -> None:
    if user.role == "student" and order.sender_id != user.id:
        raise ApiError(10003, "无权查看该订单", 403)


def add_track(
    order: ShipmentOrder, node: str, status: str, description: str | None, operator: User | None
) -> None:
    order.tracks.append(
        ShipmentTrack(
            node=node,
            status=status,
            description=description,
            operator_id=operator.id if operator else None,
            occurred_at=datetime.now(),
        )
    )


def gen_order_no(db: Session) -> str:
    prefix = datetime.now().strftime("S%Y%m%d")
    base = db.scalar(
        select(func.count()).select_from(ShipmentOrder).where(ShipmentOrder.order_no.like(f"{prefix}%"))
    ) or 0
    for offset in range(1, 12):
        candidate = f"{prefix}{base + offset:06d}"
        exists = db.scalar(select(ShipmentOrder.id).where(ShipmentOrder.order_no == candidate))
        if not exists:
            return candidate
    return f"{prefix}{secrets.randbelow(1_000_000):06d}"


@router.get("/shipments", summary="寄件订单列表")
def list_shipments(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    station_id: int | None = None,
    keyword: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(ShipmentOrder)
    if user.role == "student":
        stmt = stmt.where(ShipmentOrder.sender_id == user.id)
    if status:
        stmt = stmt.where(ShipmentOrder.status == status)
    if station_id is not None:
        stmt = stmt.where(ShipmentOrder.station_id == station_id)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                ShipmentOrder.order_no.like(like),
                ShipmentOrder.receiver_name.like(like),
                ShipmentOrder.receiver_phone.like(like),
                ShipmentOrder.item_name.like(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(
            stmt.order_by(ShipmentOrder.created_at.desc(), ShipmentOrder.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return ok(
        request,
        {
            "items": [shipment_payload(o) for o in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/shipments/summary", summary="寄件统计")
def shipments_summary(
    request: Request,
    station_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    def count(status: str) -> int:
        stmt = select(func.count()).select_from(ShipmentOrder).where(ShipmentOrder.status == status)
        if user.role == "student":
            stmt = stmt.where(ShipmentOrder.sender_id == user.id)
        if station_id is not None:
            stmt = stmt.where(ShipmentOrder.station_id == station_id)
        return int(db.scalar(stmt) or 0)

    total_stmt = select(func.count()).select_from(ShipmentOrder)
    if user.role == "student":
        total_stmt = total_stmt.where(ShipmentOrder.sender_id == user.id)
    if station_id is not None:
        total_stmt = total_stmt.where(ShipmentOrder.station_id == station_id)

    return ok(
        request,
        {
            "pending": count("pending"),
            "accepted": count("accepted"),
            "shipped": count("shipped"),
            "completed": count("completed"),
            "cancelled": count("cancelled"),
            "total": int(db.scalar(total_stmt) or 0),
        },
    )


@router.post("/shipments", summary="创建寄件订单")
def create_shipment(
    payload: ShipmentCreate,
    request: Request,
    user: User = Depends(require_roles("student")),
    db: Session = Depends(get_db),
):
    station = db.get(Station, payload.station_id)
    if station is None:
        raise ApiError(10004, "驿站不存在", 404)
    if station.status != 1:
        raise ApiError(10005, "驿站已停用，暂不能受理寄件", 409)

    order = ShipmentOrder(
        order_no=gen_order_no(db),
        sender_id=user.id,
        station_id=station.id,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        receiver_address=payload.receiver_address,
        courier_company=payload.courier_company,
        item_name=payload.item_name,
        weight=payload.weight,
        freight=calc_freight(payload.weight),
        status="pending",
        remark=payload.remark,
    )
    add_track(order, "订单已创建", "pending", f"预估运费 ¥{order.freight}", user)
    db.add(order)
    db.flush()
    push(
        db, user.id, "shipment", "寄件订单已创建",
        f"订单 {order.order_no} 已提交，请到 {station.name} 交寄，预估运费 ¥{order.freight}。",
        order_id=order.id,
    )
    db.commit()
    db.refresh(order)
    return ok(request, shipment_payload(order, detail=True), "寄件订单创建成功", 201)


@router.get("/shipments/{order_id}", summary="寄件订单详情")
def get_shipment(
    order_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)
    ensure_visible(order, user)
    return ok(request, shipment_payload(order, detail=True))


@router.get("/shipments/{order_id}/tracks", summary="寄件轨迹")
def get_tracks(
    order_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)
    ensure_visible(order, user)
    return ok(
        request,
        [
            {
                "id": t.id,
                "node": t.node,
                "status": t.status,
                "status_label": STATUS_LABEL.get(t.status, t.status),
                "description": t.description,
                "operator_name": t.operator.name if t.operator else None,
                "occurred_at": to_iso(t.occurred_at),
            }
            for t in order.tracks
        ],
    )


@router.post("/shipments/{order_id}/accept", summary="驿站揽收称重")
def accept_shipment(
    order_id: int,
    payload: ShipmentAccept,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)
    if order.status != "pending":
        raise ApiError(30001, f"订单当前为{STATUS_LABEL.get(order.status)}状态，不能揽收", 409)

    weight = payload.weight if payload.weight is not None else order.weight
    if not weight:
        raise ApiError(10001, "请填写实际重量", 422)

    order.weight = weight
    order.freight = payload.freight if payload.freight is not None else calc_freight(weight)
    if payload.courier_company:
        order.courier_company = payload.courier_company
    order.status = "accepted"
    add_track(
        order, "驿站已揽收", "accepted",
        f"实重 {order.weight} kg，运费 ¥{order.freight}", operator,
    )
    push(
        db, order.sender_id, "shipment", "包裹已揽收",
        f"订单 {order.order_no} 已在 {order.station.name if order.station else '驿站'} 揽收，"
        f"实重 {order.weight} kg，运费 ¥{order.freight}。",
        order_id=order.id,
    )
    db.commit()
    db.refresh(order)
    return ok(request, shipment_payload(order, detail=True), "揽收成功，运费已确认")


@router.post("/shipments/{order_id}/ship", summary="登记发出")
def ship_shipment(
    order_id: int,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)
    if order.status != "accepted":
        raise ApiError(30001, f"订单当前为{STATUS_LABEL.get(order.status)}状态，不能登记发出", 409)

    order.status = "shipped"
    add_track(
        order, "包裹已发出", "shipped",
        f"{order.courier_company or '承运商'} 已收件", operator,
    )
    push(
        db, order.sender_id, "shipment", "包裹已发出",
        f"订单 {order.order_no} 已交由 {order.courier_company or '承运商'} 运输。",
        order_id=order.id,
    )
    db.commit()
    db.refresh(order)
    return ok(request, shipment_payload(order, detail=True), "已登记发出")


@router.post("/shipments/{order_id}/complete", summary="确认完成")
def complete_shipment(
    order_id: int,
    request: Request,
    operator: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)
    if order.status != "shipped":
        raise ApiError(30001, f"订单当前为{STATUS_LABEL.get(order.status)}状态，不能完成", 409)

    order.status = "completed"
    add_track(order, "已签收", "completed", "收件人已签收，订单完成", operator)
    push(
        db, order.sender_id, "shipment", "包裹已签收",
        f"订单 {order.order_no} 已由收件人签收，感谢使用校园驿站。",
        order_id=order.id,
    )
    db.commit()
    db.refresh(order)
    return ok(request, shipment_payload(order, detail=True), "订单已完成")


@router.post("/shipments/{order_id}/cancel", summary="取消订单")
def cancel_shipment(
    order_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)
    if user.role == "student" and order.sender_id != user.id:
        raise ApiError(10003, "无权操作该订单", 403)
    if order.status != "pending":
        raise ApiError(30001, f"订单当前为{STATUS_LABEL.get(order.status)}状态，不能取消", 409)

    order.status = "cancelled"
    add_track(order, "订单已取消", "cancelled", "寄件人取消订单", user)
    push(
        db, order.sender_id, "shipment", "寄件订单已取消",
        f"订单 {order.order_no} 已取消。",
        order_id=order.id,
    )
    db.commit()
    db.refresh(order)
    return ok(request, shipment_payload(order, detail=True), "订单已取消")
