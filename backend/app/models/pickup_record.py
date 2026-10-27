from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PickupRecord(Base):
    """取件记录。package_id 唯一，保证一件包裹只产生一条成功出库记录。"""

    __tablename__ = "pickup_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("packages.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    pickup_code: Mapped[str] = mapped_column(String(6), nullable=False)
    phone_suffix: Mapped[str] = mapped_column(String(4), nullable=False)
    verify_type: Mapped[str] = mapped_column(String(16), nullable=False, default="code_phone")
    picked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    remark: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    package = relationship("Package", lazy="joined")
    operator = relationship("User", foreign_keys=[operator_id], lazy="joined")
