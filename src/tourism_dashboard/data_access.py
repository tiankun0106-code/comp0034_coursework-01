"""
Data access module - reads from the sqlite db and returns dicts/lists
so the Dash callbacks can consume it like a JSON API.

Built on top of the CW1 database from COMP0035.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

# path to the db file, relative to this module
_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "international_visitor_arrivals.db"


@contextmanager
def _db():
    """Quick helper to get a db connection that auto-closes."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _rows_to_dicts(cursor):
    return [dict(r) for r in cursor.fetchall()]


def _add_year_filters(query, params, start_year, end_year):
    """Append year filter clauses to a query. Modifies params in place."""
    if start_year is not None:
        query += "AND tp.year >= ? "
        params.append(start_year)
    if end_year is not None:
        query += "AND tp.year <= ? "
        params.append(end_year)
    return query


# ---- simple lookups --------------------------------------------------------

def get_categories():
    """Return all market categories sorted by name."""
    with _db() as conn:
        cur = conn.execute(
            "SELECT category_id, category_name, category_description "
            "FROM MarketCategory ORDER BY category_name"
        )
        return _rows_to_dicts(cur)


def get_markets(category_id=None):
    """Get markets, optionally filtering by category_id."""
    with _db() as conn:
        if category_id is not None:
            cur = conn.execute(
                "SELECT market_id, market_name, category_id, is_active "
                "FROM Market WHERE category_id = ? ORDER BY market_name",
                (category_id,),
            )
        else:
            cur = conn.execute(
                "SELECT market_id, market_name, category_id, is_active "
                "FROM Market ORDER BY market_name"
            )
        return _rows_to_dicts(cur)


def get_individual_markets():
    """Only real country markets (skip the aggregate rows like 'Southeast Asia' total)."""
    # category_id 1 and 2 are totals/aggregates in this dataset
    with _db() as conn:
        cur = conn.execute(
            "SELECT m.market_id, m.market_name, mc.category_name "
            "FROM Market m "
            "JOIN MarketCategory mc ON m.category_id = mc.category_id "
            "WHERE m.category_id >= 3 "
            "ORDER BY mc.category_name, m.market_name"
        )
        return _rows_to_dicts(cur)


def get_year_range():
    """Returns {'min_year': ..., 'max_year': ...} from TimePeriod table."""
    with _db() as conn:
        row = conn.execute("SELECT MIN(year), MAX(year) FROM TimePeriod").fetchone()
        return {"min_year": row[0], "max_year": row[1]}


# ---- time series & aggregations -------------------------------------------

def get_arrivals_time_series(market_ids, start_year=None, end_year=None):
    """Monthly arrivals for the given market ids. Returns [] if no ids given."""
    if not market_ids:
        return []

    with _db() as conn:
        ph = ",".join("?" for _ in market_ids)
        q = (
            "SELECT m.market_name, tp.year, tp.month, va.arrival_count "
            "FROM VisitorArrival va "
            "JOIN Market m ON va.market_id = m.market_id "
            "JOIN TimePeriod tp ON va.period_id = tp.period_id "
            f"WHERE va.market_id IN ({ph}) "
            "AND va.arrival_count IS NOT NULL "
        )
        params = list(market_ids)
        q = _add_year_filters(q, params, start_year, end_year)
        q += "ORDER BY tp.year, tp.month, m.market_name"
        return _rows_to_dicts(conn.execute(q, params))


def get_top_markets(n=10, start_year=None, end_year=None):
    """Top n markets ranked by total arrivals (excludes aggregate rows)."""
    with _db() as conn:
        q = (
            "SELECT m.market_name, SUM(va.arrival_count) AS total_arrivals, "
            "mc.category_name "
            "FROM VisitorArrival va "
            "JOIN Market m ON va.market_id = m.market_id "
            "JOIN MarketCategory mc ON m.category_id = mc.category_id "
            "JOIN TimePeriod tp ON va.period_id = tp.period_id "
            "WHERE va.arrival_count IS NOT NULL "
            "AND m.category_id >= 3 "
        )
        params = []
        q = _add_year_filters(q, params, start_year, end_year)
        q += "GROUP BY m.market_id ORDER BY total_arrivals DESC LIMIT ?"
        params.append(n)
        return _rows_to_dicts(conn.execute(q, params))


def get_seasonal_heatmap_data(market_id, start_year=None, end_year=None):
    """For the heatmap chart - returns year/month/arrival_count rows."""
    with _db() as conn:
        q = (
            "SELECT tp.year, tp.month, mr.month_abbrev AS month_name, "
            "va.arrival_count "
            "FROM VisitorArrival va "
            "JOIN TimePeriod tp ON va.period_id = tp.period_id "
            "JOIN MonthReference mr ON tp.month = mr.month_number "
            "WHERE va.market_id = ? AND va.arrival_count IS NOT NULL "
        )
        params = [market_id]
        q = _add_year_filters(q, params, start_year, end_year)
        q += "ORDER BY tp.year, tp.month"
        return _rows_to_dicts(conn.execute(q, params))


def get_category_share(start_year=None, end_year=None):
    """Totals per region for the pie chart."""
    with _db() as conn:
        q = (
            "SELECT mc.category_name, SUM(va.arrival_count) AS total_arrivals "
            "FROM VisitorArrival va "
            "JOIN Market m ON va.market_id = m.market_id "
            "JOIN MarketCategory mc ON m.category_id = mc.category_id "
            "JOIN TimePeriod tp ON va.period_id = tp.period_id "
            "WHERE va.arrival_count IS NOT NULL AND m.category_id >= 3 "
        )
        params = []
        q = _add_year_filters(q, params, start_year, end_year)
        q += "GROUP BY mc.category_name ORDER BY total_arrivals DESC"
        return _rows_to_dicts(conn.execute(q, params))


def get_yearly_totals(market_id=None):
    """Yearly sums. If market_id given, only that market; otherwise all individual markets."""
    with _db() as conn:
        if market_id is not None:
            cur = conn.execute(
                "SELECT tp.year, SUM(va.arrival_count) AS total_arrivals "
                "FROM VisitorArrival va "
                "JOIN TimePeriod tp ON va.period_id = tp.period_id "
                "WHERE va.market_id = ? AND va.arrival_count IS NOT NULL "
                "GROUP BY tp.year ORDER BY tp.year",
                (market_id,)
            )
        else:
            cur = conn.execute(
                "SELECT tp.year, SUM(va.arrival_count) AS total_arrivals "
                "FROM VisitorArrival va "
                "JOIN Market m ON va.market_id = m.market_id "
                "JOIN TimePeriod tp ON va.period_id = tp.period_id "
                "WHERE va.arrival_count IS NOT NULL AND m.category_id >= 3 "
                "GROUP BY tp.year ORDER BY tp.year"
            )
        return _rows_to_dicts(cur)


# ---- data explorer / detail view ------------------------------------------

def get_market_detail_table(market_ids, start_year=None, end_year=None):
    """Detailed rows for the DataTable in the explorer page."""
    if not market_ids:
        return []

    with _db() as conn:
        ph = ",".join("?" for _ in market_ids)
        q = (
            "SELECT m.market_name AS Market, mc.category_name AS Category, "
            "tp.year AS Year, mr.month_name AS Month, tp.month AS MonthNum, "
            "va.arrival_count AS Arrivals, va.data_quality_flag AS Quality "
            "FROM VisitorArrival va "
            "JOIN Market m ON va.market_id = m.market_id "
            "JOIN MarketCategory mc ON m.category_id = mc.category_id "
            "JOIN TimePeriod tp ON va.period_id = tp.period_id "
            "JOIN MonthReference mr ON tp.month = mr.month_number "
            f"WHERE va.market_id IN ({ph}) "
        )
        params = list(market_ids)
        q = _add_year_filters(q, params, start_year, end_year)
        q += "ORDER BY tp.year DESC, tp.month DESC, m.market_name"
        return _rows_to_dicts(conn.execute(q, params))


# ---- recovery comparison --------------------------------------------------

def get_recovery_comparison(market_ids, baseline_year=2019, comparison_year=2024):
    """
    Compares two years side by side for each market.
    Used for the covid recovery feature.
    """
    if not market_ids:
        return []

    with _db() as conn:
        ph = ",".join("?" for _ in market_ids)
        q = (
            "SELECT m.market_name, tp.year, SUM(va.arrival_count) AS total "
            "FROM VisitorArrival va "
            "JOIN Market m ON va.market_id = m.market_id "
            "JOIN TimePeriod tp ON va.period_id = tp.period_id "
            f"WHERE va.market_id IN ({ph}) "
            "AND tp.year IN (?, ?) "
            "AND va.arrival_count IS NOT NULL "
            "GROUP BY m.market_name, tp.year"
        )
        params = list(market_ids) + [baseline_year, comparison_year]
        rows = _rows_to_dicts(conn.execute(q, params))

    # pivot into {market: {baseline: x, comparison: y}} shape
    by_market = {}
    for r in rows:
        name = r["market_name"]
        if name not in by_market:
            by_market[name] = {"market_name": name, "baseline_total": 0, "comparison_total": 0}
        if r["year"] == baseline_year:
            by_market[name]["baseline_total"] = r["total"]
        else:
            by_market[name]["comparison_total"] = r["total"]

    # calculate recovery percentage
    out = []
    for d in by_market.values():
        if d["baseline_total"] > 0:
            d["recovery_pct"] = round(d["comparison_total"] / d["baseline_total"] * 100, 1)
        else:
            d["recovery_pct"] = None
        out.append(d)

    # sort best recovery first
    return sorted(out, key=lambda x: x.get("recovery_pct") or 0, reverse=True)
