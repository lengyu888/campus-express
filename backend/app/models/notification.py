from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

# pickup 取件 / overdue 超期 / shipment 寄件 / system 系统
NOTIFICATION_TYPES = ("pickup", "overdue", "shipment", "system")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "is_read"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="system", index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    package_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    order_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False, default="inapp")
    is_read: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
