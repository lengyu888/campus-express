"""站内通知与运费估算的公共逻辑。"""
import math
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.notification import Notification


def calc_freight(weight: Decimal | float | None) -> Decimal:
    """首重 1 kg 8 元，续重每 1 kg 加 2 元，不足 1 kg 按 1 kg 计。"""
    if not weight or float(weight) <= 0:
        return Decimal("0.00")
    kg = max(1, math.ceil(float(weight)))
    return Decimal("8.00") + Decimal("2.00") * (kg - 1)


def push(
    db: Session,
    user_id: int | None,
    type_: str,
    title: str,
    content: str,
    package_id: int | None = None,
    order_id: int | None = None,
) -> None:
    """写入站内通知，由调用方统一提交事务。"""
    if not user_id:
        return
    db.add(
        Notification(
            user_id=user_id,
            type=type_,
            title=title,
            content=content,
            package_id=package_id,
            order_id=order_id,
            channel="inapp",
            is_read=0,
            sent_at=datetime.now(),
        )
    )
