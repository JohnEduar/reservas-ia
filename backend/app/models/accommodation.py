from datetime import date as date_type
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

accommodation_amenities = Table(
    "accommodation_amenities",
    Base.metadata,
    Column(
        "accommodation_id",
        Integer,
        ForeignKey("accommodations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "amenity_id",
        Integer,
        ForeignKey("amenities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Amenity(Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)

    accommodations: Mapped[list["Accommodation"]] = relationship(
        "Accommodation",
        secondary=accommodation_amenities,
        back_populates="amenities",
    )


class Accommodation(Base):
    __tablename__ = "accommodations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    images: Mapped[list["AccommodationImage"]] = relationship(
        "AccommodationImage",
        back_populates="accommodation",
        cascade="all, delete-orphan",
        order_by="AccommodationImage.sort_order",
    )
    amenities: Mapped[list["Amenity"]] = relationship(
        "Amenity",
        secondary=accommodation_amenities,
        back_populates="accommodations",
    )
    blocked_dates: Mapped[list["AccommodationAvailability"]] = relationship(
        "AccommodationAvailability",
        back_populates="accommodation",
        cascade="all, delete-orphan",
    )
    seasonal_prices: Mapped[list["SeasonalPrice"]] = relationship(
        "SeasonalPrice",
        back_populates="accommodation",
        cascade="all, delete-orphan",
        order_by="SeasonalPrice.start_date",
    )


class AccommodationImage(Base):
    __tablename__ = "accommodation_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    accommodation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accommodations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    accommodation: Mapped["Accommodation"] = relationship(
        "Accommodation", back_populates="images"
    )


class AccommodationAvailability(Base):
    """Each row represents a blocked (unavailable) date for an accommodation."""

    __tablename__ = "accommodation_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    accommodation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accommodations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("accommodation_id", "date", name="uq_availability_acc_date"),
    )

    accommodation: Mapped["Accommodation"] = relationship(
        "Accommodation", back_populates="blocked_dates"
    )


class SeasonalPrice(Base):
    """Price override for a specific date range (e.g., peak season, holiday)."""

    __tablename__ = "seasonal_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    accommodation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accommodations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    end_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    accommodation: Mapped["Accommodation"] = relationship(
        "Accommodation", back_populates="seasonal_prices"
    )
