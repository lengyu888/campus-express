from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Numeric, String, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# pending 待揽收 / accepted 已揽收 / shipped 已发出 / completed 已完成 / cancelled 已取消
SHIPMENT_STATUS = ("pending", "accepted", "shipped", "completed", "cancelled")


class ShipmentOrder(Base):
    __tablename__ = "shipment_orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    sender_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    station_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False
    )
    receiver_name: Mapped[str] = mapped_column(String(50), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(11), nullable=False)
    receiver_address: Mapped[str] = mapped_column(String(200), nullable=False)
    courier_company: Mapped[str | None] = mapped_column(String(30), nullable=True)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    freight: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    sender = relationship("User", foreign_keys=[sender_id], lazy="joined")
    station = relationship("Station", lazy="joined")
    tracks = relationship(
        "ShipmentTrack", back_populates="order", cascade="all, delete-orphan",
        order_by="ShipmentTrack.occurred_at", lazy="selectin",
    )


class ShipmentTrack(Base):
    __tablename__ = "shipment_tracks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("shipment_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    order = relationship("ShipmentOrder", back_populates="tracks")
    operator = relationship("User", foreign_keys=[operator_id], lazy="joined")
