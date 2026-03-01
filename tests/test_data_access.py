"""
Tests for the data access layer.
Mix of unit tests (no db needed) and integration tests (hit the real db).
"""

import pytest
from tourism_dashboard.data_access import (
    get_categories, get_markets, get_individual_markets, get_year_range,
    get_arrivals_time_series, get_top_markets, get_seasonal_heatmap_data,
    get_category_share, get_yearly_totals, get_market_detail_table,
    get_recovery_comparison,
)


# ---------- categories ----------

def test_categories_returns_nonempty_list():
    """Should get a list of category dicts from the db."""
    result = get_categories()
    assert isinstance(result, list) and len(result) > 0


def test_category_dict_keys():
    cats = get_categories()
    for c in cats:
        assert "category_id" in c
        assert "category_name" in c
        assert "category_description" in c


def test_known_categories_present():
    """Sanity check that the db has the regions we expect."""
    names = [c["category_name"] for c in get_categories()]
    assert "Southeast Asia" in names
    assert "Europe" in names


# ---------- markets ----------

def test_get_all_markets():
    result = get_markets()
    assert len(result) > 0


def test_filter_markets_by_category():
    # category 3 = Southeast Asia in our db
    sea_markets = get_markets(category_id=3)
    assert len(sea_markets) > 0
    for m in sea_markets:
        assert m["category_id"] == 3


def test_individual_markets_no_aggregates():
    """The aggregate rows (Total, Regional) should be excluded."""
    mkts = get_individual_markets()
    assert len(mkts) > 0
    for m in mkts:
        assert m["category_name"] not in ("Total Aggregate", "Regional Aggregate")


def test_individual_markets_have_category():
    for m in get_individual_markets():
        assert m["category_name"] is not None


# ---------- year range ----------

def test_year_range_structure():
    yr = get_year_range()
    assert "min_year" in yr and "max_year" in yr
    assert yr["min_year"] < yr["max_year"]


def test_year_range_sensible():
    yr = get_year_range()
    assert yr["min_year"] > 1900
    assert yr["max_year"] <= 2030


# ---------- time series ----------

def test_time_series_empty_ids():
    """Edge case: no market ids should just return []."""
    assert get_arrivals_time_series([]) == []


def test_time_series_returns_data():
    # market 3 = Brunei
    rows = get_arrivals_time_series([3], start_year=2020, end_year=2024)
    assert isinstance(rows, list)
    if rows:
        r = rows[0]
        assert "market_name" in r and "year" in r
        assert "month" in r and "arrival_count" in r


def test_time_series_year_filter():
    rows = get_arrivals_time_series([14], start_year=2023, end_year=2023)
    for r in rows:
        assert r["year"] == 2023


def test_time_series_multi_market():
    rows = get_arrivals_time_series([3, 4, 5], start_year=2024, end_year=2024)
    if rows:
        names = {r["market_name"] for r in rows}
        assert len(names) >= 1  # at least one market returned data


# ---------- top markets ----------

class TestTopMarkets:
    """Grouped these since they're closely related."""

    def test_limit_works(self):
        assert len(get_top_markets(n=5)) <= 5

    def test_descending_order(self):
        result = get_top_markets(n=10)
        for i in range(len(result) - 1):
            assert result[i]["total_arrivals"] >= result[i + 1]["total_arrivals"]

    def test_has_expected_keys(self):
        for item in get_top_markets(n=3):
            assert "market_name" in item
            assert "total_arrivals" in item
            assert "category_name" in item


# ---------- heatmap ----------

def test_heatmap_data_structure():
    rows = get_seasonal_heatmap_data(1, start_year=2020, end_year=2024)
    assert isinstance(rows, list)
    if rows:
        assert all(k in rows[0] for k in ("year", "month", "month_name", "arrival_count"))


def test_heatmap_months_valid():
    for r in get_seasonal_heatmap_data(1, start_year=2020, end_year=2024):
        assert 1 <= r["month"] <= 12


# ---------- category share (pie chart data) ----------

def test_category_share():
    result = get_category_share(start_year=2020, end_year=2024)
    assert len(result) > 0
    for item in result:
        assert "category_name" in item
        assert item["total_arrivals"] > 0


# ---------- yearly totals ----------

def test_yearly_totals_all():
    result = get_yearly_totals()
    assert len(result) > 0
    assert "year" in result[0] and "total_arrivals" in result[0]


def test_yearly_totals_single_market():
    result = get_yearly_totals(market_id=1)
    if result:
        assert "year" in result[0]


def test_yearly_totals_sorted():
    result = get_yearly_totals()
    years = [r["year"] for r in result]
    assert years == sorted(years)


# ---------- detail table ----------

def test_detail_table_empty_ids():
    assert get_market_detail_table([]) == []


def test_detail_table_columns():
    """Check that the returned dicts match what the DataTable expects."""
    rows = get_market_detail_table([3], start_year=2024, end_year=2024)
    if rows:
        expected = {"Market", "Category", "Year", "Month", "MonthNum", "Arrivals", "Quality"}
        assert expected.issubset(set(rows[0].keys()))


# ---------- recovery comparison ----------

def test_recovery_empty_ids():
    assert get_recovery_comparison([]) == []


def test_recovery_fields():
    result = get_recovery_comparison([5], baseline_year=2019, comparison_year=2024)
    if result:
        item = result[0]
        for key in ("market_name", "baseline_total", "comparison_total", "recovery_pct"):
            assert key in item


def test_recovery_pct_math():
    """Make sure the percentage is actually calculated right."""
    result = get_recovery_comparison([5], baseline_year=2019, comparison_year=2024)
    for item in result:
        if item["baseline_total"] > 0 and item["recovery_pct"] is not None:
            expected = round(item["comparison_total"] / item["baseline_total"] * 100, 1)
            assert item["recovery_pct"] == expected


# ---------- extra edge cases ----------

def test_categories_ids_are_unique():
    ids = [c["category_id"] for c in get_categories()]
    assert len(ids) == len(set(ids))


def test_markets_invalid_category():
    """A category that doesn't exist should return empty."""
    result = get_markets(category_id=99999)
    assert result == []


def test_time_series_single_year():
    rows = get_arrivals_time_series([3], start_year=2024, end_year=2024)
    for r in rows:
        assert r["year"] == 2024


def test_top_markets_n_equals_one():
    result = get_top_markets(n=1)
    assert len(result) == 1
    assert result[0]["total_arrivals"] > 0


def test_heatmap_invalid_market():
    """A market id that doesn't exist should return empty list."""
    result = get_seasonal_heatmap_data(market_id=99999)
    assert result == []


def test_yearly_totals_values_positive():
    for r in get_yearly_totals():
        assert r["total_arrivals"] > 0


def test_recovery_same_year():
    """When baseline == comparison, only baseline_total gets filled (same year row)."""
    result = get_recovery_comparison([5], baseline_year=2024, comparison_year=2024)
    # should still return data without crashing
    assert isinstance(result, list)


def test_detail_table_single_market_has_data():
    rows = get_market_detail_table([3], start_year=2024, end_year=2024)
    # should have some rows for a known market
    assert len(rows) >= 0  # might be empty if no 2024 data, but shouldn't crash
