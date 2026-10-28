from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# open 待处理 / processing 处理中 / resolved 已解决
EXCEPTION_STATUS = ("open", "processing", "resolved")
EXCEPTION_TYPES = ("damaged", "lost", "wrong_station", "returned", "other")


class ExceptionRecord(Base):
    __tablename__ = "exception_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("packages.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="other", index=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    handler_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    package = relationship("Package", lazy="joined")
    handler = relationship("User", foreign_keys=[handler_id], lazy="joined")
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
