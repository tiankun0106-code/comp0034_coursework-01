"""Pydantic schemas for request/response validation."""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict

# ---- Category Schemas ----

class CategoryResponse(BaseModel):
    category_id: int
    category_name: str
    category_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---- Market Schemas ----

class MarketResponse(BaseModel):
    market_id: int
    market_name: str
    category_id: int
    category_name: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class MarketCreate(BaseModel):
    market_name: str
    category_id: int
    is_active: bool = True


class MarketUpdate(BaseModel):
    market_name: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


# ---- Arrival Data Schemas ----

class ArrivalTimeSeriesResponse(BaseModel):
    market_name: str
    year: int
    month: int
    arrival_count: int

    model_config = ConfigDict(from_attributes=True)


class TopMarketResponse(BaseModel):
    market_name: str
    total_arrivals: int
    category_name: str

    model_config = ConfigDict(from_attributes=True)


class HeatmapDataResponse(BaseModel):
    year: int
    month: int
    month_name: str
    arrival_count: int
    model_config = ConfigDict(from_attributes=True)


class CategoryShareResponse(BaseModel):
    category_name: str
    total_arrivals: int

    model_config = ConfigDict(from_attributes=True)


class YearlyTotalResponse(BaseModel):
    year: int
    total_arrivals: int

    model_config = ConfigDict(from_attributes=True)


class MarketDetailResponse(BaseModel):
    Market: str
    Category: str
    Year: int
    Month: str
    MonthNum: int
    Arrivals: int
    Quality: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class RecoveryComparisonResponse(BaseModel):
    market_name: str
    baseline_total: int
    comparison_total: int
    recovery_pct: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ---- Query Parameter Schemas ----

class YearRangeQuery(BaseModel):
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class MarketListQuery(BaseModel):
    market_ids: List[int]
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class RecoveryQuery(BaseModel):
    market_ids: List[int]
    baseline_year: int = 2019
    comparison_year: int = 2024
