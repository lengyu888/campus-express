from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Package(Base):
    """快递包裹。status 取值 in_stock / picked / overdue / returned / exception。"""

    __tablename__ = "packages"
    __table_args__ = (
        UniqueConstraint("station_id", "pickup_code", name="uk_packages_station_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tracking_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    station_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    shelf_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recipient_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recipient_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recipient_phone: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    courier_company: Mapped[str] = mapped_column(String(30), nullable=False)
    package_type: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="in_stock", index=True)
    pickup_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    code_expire_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    stored_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    picked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    overdue_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    station = relationship("Station", lazy="joined")
    shelf = relationship("Shelf", lazy="joined")
    recipient = relationship("User", foreign_keys=[recipient_id], lazy="joined")
    operator = relationship("User", foreign_keys=[created_by], lazy="joined")
