from datetime import datetime, time

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, Time, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(11), nullable=True)
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manager_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    manager = relationship("User", foreign_keys=[manager_id], lazy="joined")
    shelves = relationship(
        "Shelf", back_populates="station", cascade="all, delete-orphan", lazy="selectin"
    )
