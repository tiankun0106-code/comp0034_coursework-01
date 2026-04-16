"""SQLModel ORM models mapping to database tables."""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class MarketCategory(SQLModel, table=True):
    """Market category model."""
    __tablename__ = "MarketCategory"

    category_id: int = Field(default=None, primary_key=True)
    category_name: str
    category_description: Optional[str] = None
    created_date: Optional[datetime] = None


class Market(SQLModel, table=True):
    """Market model."""
    __tablename__ = "Market"

    market_id: int = Field(default=None, primary_key=True)
    market_name: str
    category_id: int = Field(foreign_key="MarketCategory.category_id")
    is_active: bool = True
    created_date: Optional[datetime] = None


class TimePeriod(SQLModel, table=True):
    """Time period model."""
    __tablename__ = "TimePeriod"

    period_id: int = Field(default=None, primary_key=True)
    year: int
    month: int
    created_date: Optional[datetime] = None


class MonthReference(SQLModel, table=True):
    """Month reference model."""
    __tablename__ = "MonthReference"

    month_number: int = Field(default=None, primary_key=True)
    month_name: str
    month_abbrev: str
    quarter: Optional[int] = None
    days_count: Optional[int] = None


class VisitorArrival(SQLModel, table=True):
    """Visitor arrival model."""
    __tablename__ = "VisitorArrival"

    arrival_id: int = Field(default=None, primary_key=True)
    market_id: int = Field(foreign_key="Market.market_id")
    period_id: int = Field(foreign_key="TimePeriod.period_id")
    arrival_count: Optional[int] = None
    is_estimated: Optional[bool] = None
    data_quality_flag: Optional[str] = None
    created_date: Optional[datetime] = None