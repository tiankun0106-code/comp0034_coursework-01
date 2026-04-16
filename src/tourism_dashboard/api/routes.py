"""REST API routes for tourism data."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session, select, func
from sqlalchemy import and_

from tourism_dashboard.api.database import get_session
from tourism_dashboard.api.models import MarketCategory, Market, TimePeriod, MonthReference, VisitorArrival
from tourism_dashboard.api.schemas import (
    CategoryResponse,
    MarketResponse,
    ArrivalTimeSeriesResponse,
    TopMarketResponse,
    HeatmapDataResponse,
    CategoryShareResponse,
    YearlyTotalResponse,
    MarketDetailResponse,
    RecoveryComparisonResponse,
    MarketCreate,
    MarketUpdate,
)

router = APIRouter()


# ---- Helper functions ----

def _add_year_filters(query, start_year: Optional[int], end_year: Optional[int]):
    """Add year filter conditions to a query."""
    if start_year is not None:
        query = query.where(TimePeriod.year >= start_year)
    if end_year is not None:
        query = query.where(TimePeriod.year <= end_year)
    return query


# ---- GET Routes ----

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(session: Session = Depends(get_session)):
    """Get all market categories."""
    statement = select(MarketCategory).order_by(MarketCategory.category_name)
    results = session.exec(statement).all()
    return results


@router.get("/markets", response_model=List[MarketResponse])
def get_markets(
    category_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Get markets, optionally filtered by category."""
    statement = select(Market, MarketCategory.category_name).join(
        MarketCategory, Market.category_id == MarketCategory.category_id
    )
    
    if category_id is not None:
        statement = statement.where(Market.category_id == category_id)
    
    statement = statement.order_by(Market.market_name)
    results = session.exec(statement).all()
    
    return [
        MarketResponse(
            market_id=m.market_id,
            market_name=m.market_name,
            category_id=m.category_id,
            category_name=cat_name,
            is_active=m.is_active
        )
        for m, cat_name in results
    ]


@router.get("/markets/individual", response_model=List[MarketResponse])
def get_individual_markets(session: Session = Depends(get_session)):
    """Get individual markets (exclude aggregate rows)."""
    statement = (
        select(Market, MarketCategory.category_name)
        .join(MarketCategory, Market.category_id == MarketCategory.category_id)
        .where(Market.category_id >= 3)
        .order_by(MarketCategory.category_name, Market.market_name)
    )
    results = session.exec(statement).all()
    
    return [
        MarketResponse(
            market_id=m.market_id,
            market_name=m.market_name,
            category_id=m.category_id,
            category_name=cat_name,
            is_active=m.is_active
        )
        for m, cat_name in results
    ]


@router.get("/year-range")
def get_year_range(session: Session = Depends(get_session)):
    """Get min and max year from the database."""
    min_year = session.exec(select(func.min(TimePeriod.year))).one()
    max_year = session.exec(select(func.max(TimePeriod.year))).one()
    return {"min_year": min_year, "max_year": max_year}


@router.get("/arrivals/time-series", response_model=List[ArrivalTimeSeriesResponse])
def get_arrivals_time_series(
    market_ids: List[int] = Query(...),
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Get monthly arrivals for specified markets."""
    if not market_ids:
        return []
    
    statement = (
        select(
            Market.market_name,
            TimePeriod.year,
            TimePeriod.month,
            VisitorArrival.arrival_count
        )
        .join(Market, VisitorArrival.market_id == Market.market_id)
        .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
        .where(
            and_(
                VisitorArrival.market_id.in_(market_ids),
                VisitorArrival.arrival_count.isnot(None)
            )
        )
    )
    
    statement = _add_year_filters(statement, start_year, end_year)
    statement = statement.order_by(TimePeriod.year, TimePeriod.month, Market.market_name)
    
    results = session.exec(statement).all()
    return [
        ArrivalTimeSeriesResponse(
            market_name=row[0],
            year=row[1],
            month=row[2],
            arrival_count=row[3]
        )
        for row in results
    ]


@router.get("/markets/top", response_model=List[TopMarketResponse])
def get_top_markets(
    n: int = Query(10, ge=1, le=100),
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Get top N markets by total arrivals."""
    statement = (
        select(
            Market.market_name,
            func.sum(VisitorArrival.arrival_count).label("total_arrivals"),
            MarketCategory.category_name
        )
        .join(Market, VisitorArrival.market_id == Market.market_id)
        .join(MarketCategory, Market.category_id == MarketCategory.category_id)
        .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
        .where(
            and_(
                VisitorArrival.arrival_count.isnot(None),
                Market.category_id >= 3
            )
        )
    )
    
    statement = _add_year_filters(statement, start_year, end_year)
    statement = (
        statement
        .group_by(Market.market_id, Market.market_name, MarketCategory.category_name)
        .order_by(func.sum(VisitorArrival.arrival_count).desc())
        .limit(n)
    )
    
    results = session.exec(statement).all()
    return [
        TopMarketResponse(
            market_name=row[0],
            total_arrivals=row[1],
            category_name=row[2]
        )
        for row in results
    ]


@router.get("/arrivals/heatmap", response_model=List[HeatmapDataResponse])
def get_seasonal_heatmap_data(
    market_id: int = Query(...),
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Get data for seasonal heatmap."""
    statement = (
        select(
            TimePeriod.year,
            TimePeriod.month,
            MonthReference.month_abbrev.label("month_name"),
            VisitorArrival.arrival_count
        )
        .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
        .join(MonthReference, TimePeriod.month == MonthReference.month_number)
        .where(
            and_(
                VisitorArrival.market_id == market_id,
                VisitorArrival.arrival_count.isnot(None)
            )
        )
    )
    
    statement = _add_year_filters(statement, start_year, end_year)
    statement = statement.order_by(TimePeriod.year, TimePeriod.month)
    
    results = session.exec(statement).all()
    return [
        HeatmapDataResponse(
            year=row[0],
            month=row[1],
            month_name=row[2],
            arrival_count=row[3]
        )
        for row in results
    ]


@router.get("/categories/share", response_model=List[CategoryShareResponse])
def get_category_share(
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Get total arrivals per region/category."""
    statement = (
        select(
            MarketCategory.category_name,
            func.sum(VisitorArrival.arrival_count).label("total_arrivals")
        )
        .join(Market, VisitorArrival.market_id == Market.market_id)
        .join(MarketCategory, Market.category_id == MarketCategory.category_id)
        .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
        .where(
            and_(
                VisitorArrival.arrival_count.isnot(None),
                Market.category_id >= 3
            )
        )
    )
    
    statement = _add_year_filters(statement, start_year, end_year)
    statement = (
        statement
        .group_by(MarketCategory.category_name)
        .order_by(func.sum(VisitorArrival.arrival_count).desc())
    )
    
    results = session.exec(statement).all()
    return [
        CategoryShareResponse(
            category_name=row[0],
            total_arrivals=row[1]
        )
        for row in results
    ]


@router.get("/arrivals/yearly", response_model=List[YearlyTotalResponse])
def get_yearly_totals(
    market_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Get yearly total arrivals."""
    if market_id is not None:
        statement = (
            select(
                TimePeriod.year,
                func.sum(VisitorArrival.arrival_count).label("total_arrivals")
            )
            .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
            .where(
                and_(
                    VisitorArrival.market_id == market_id,
                    VisitorArrival.arrival_count.isnot(None)
                )
            )
            .group_by(TimePeriod.year)
            .order_by(TimePeriod.year)
        )
    else:
        statement = (
            select(
                TimePeriod.year,
                func.sum(VisitorArrival.arrival_count).label("total_arrivals")
            )
            .join(Market, VisitorArrival.market_id == Market.market_id)
            .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
            .where(
                and_(
                    VisitorArrival.arrival_count.isnot(None),
                    Market.category_id >= 3
                )
            )
            .group_by(TimePeriod.year)
            .order_by(TimePeriod.year)
        )
    
    results = session.exec(statement).all()
    return [
        YearlyTotalResponse(year=row[0], total_arrivals=row[1])
        for row in results
    ]


@router.get("/markets/detail", response_model=List[MarketDetailResponse])
def get_market_detail_table(
    market_ids: List[int] = Query(...),
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Get detailed market data for table display."""
    if not market_ids:
        return []
    
    statement = (
        select(
            Market.market_name.label("Market"),
            MarketCategory.category_name.label("Category"),
            TimePeriod.year.label("Year"),
            MonthReference.month_name.label("Month"),
            TimePeriod.month.label("MonthNum"),
            VisitorArrival.arrival_count.label("Arrivals"),
            VisitorArrival.data_quality_flag.label("Quality")
        )
        .join(Market, VisitorArrival.market_id == Market.market_id)
        .join(MarketCategory, Market.category_id == MarketCategory.category_id)
        .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
        .join(MonthReference, TimePeriod.month == MonthReference.month_number)
        .where(VisitorArrival.market_id.in_(market_ids))
    )
    
    statement = _add_year_filters(statement, start_year, end_year)
    statement = statement.order_by(
        TimePeriod.year.desc(),
        TimePeriod.month.desc(),
        Market.market_name
    )
    
    results = session.exec(statement).all()
    return [
        MarketDetailResponse(
            Market=row[0],
            Category=row[1],
            Year=row[2],
            Month=row[3],
            MonthNum=row[4],
            Arrivals=row[5],
            Quality=row[6]
        )
        for row in results
    ]


@router.get("/recovery/comparison", response_model=List[RecoveryComparisonResponse])
def get_recovery_comparison(
    market_ids: List[int] = Query(...),
    baseline_year: int = Query(2019),
    comparison_year: int = Query(2024),
    session: Session = Depends(get_session)
):
    """Compare arrivals between baseline and comparison years."""
    if not market_ids:
        return []
    
    statement = (
        select(
            Market.market_name,
            TimePeriod.year,
            func.sum(VisitorArrival.arrival_count).label("total")
        )
        .join(Market, VisitorArrival.market_id == Market.market_id)
        .join(TimePeriod, VisitorArrival.period_id == TimePeriod.period_id)
        .where(
            and_(
                VisitorArrival.market_id.in_(market_ids),
                TimePeriod.year.in_([baseline_year, comparison_year]),
                VisitorArrival.arrival_count.isnot(None)
            )
        )
        .group_by(Market.market_name, TimePeriod.year)
    )
    
    results = session.exec(statement).all()
    
    # Pivot data into market-level summary
    by_market = {}
    for row in results:
        name = row[0]
        if name not in by_market:
            by_market[name] = {
                "market_name": name,
                "baseline_total": 0,
                "comparison_total": 0
            }
        if row[1] == baseline_year:
            by_market[name]["baseline_total"] = row[2]
        else:
            by_market[name]["comparison_total"] = row[2]
    
    # Calculate recovery percentage
    output = []
    for data in by_market.values():
        if data["baseline_total"] > 0:
            data["recovery_pct"] = round(
                data["comparison_total"] / data["baseline_total"] * 100, 1
            )
        else:
            data["recovery_pct"] = None
        output.append(data)
    
    # Sort by recovery percentage (best first)
    output.sort(key=lambda x: x.get("recovery_pct") or 0, reverse=True)
    
    return [
        RecoveryComparisonResponse(**item)
        for item in output
    ]


# ---- POST Route ----

@router.post("/markets", response_model=MarketResponse, status_code=201)
def create_market(market: MarketCreate, session: Session = Depends(get_session)):
    """Create a new market."""
    db_market = Market(
        market_name=market.market_name,
        category_id=market.category_id,
        is_active=market.is_active
    )
    session.add(db_market)
    session.commit()
    session.refresh(db_market)
    
    # Get category name
    category = session.get(MarketCategory, db_market.category_id)
    
    return MarketResponse(
        market_id=db_market.market_id,
        market_name=db_market.market_name,
        category_id=db_market.category_id,
        category_name=category.category_name if category else None,
        is_active=db_market.is_active
    )


# ---- PUT/PATCH Route ----

@router.patch("/markets/{market_id}", response_model=MarketResponse)
def update_market(
    market_id: int,
    market_update: MarketUpdate,
    session: Session = Depends(get_session)
):
    """Update an existing market (partial update)."""
    db_market = session.get(Market, market_id)
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    update_data = market_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_market, key, value)
    
    session.add(db_market)
    session.commit()
    session.refresh(db_market)
    
    # Get category name
    category = session.get(MarketCategory, db_market.category_id)
    
    return MarketResponse(
        market_id=db_market.market_id,
        market_name=db_market.market_name,
        category_id=db_market.category_id,
        category_name=category.category_name if category else None,
        is_active=db_market.is_active
    )


# ---- DELETE Route ----

@router.delete("/markets/{market_id}", status_code=204)
def delete_market(market_id: int, session: Session = Depends(get_session)):
    """Delete a market."""
    db_market = session.get(Market, market_id)
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    session.delete(db_market)
    session.commit()
    return None
