"""
Data access module - retrieves data from the FastAPI REST backend.
Replaces direct database access with HTTP API calls.

Built on top of the CW1 database from COMP0035 via REST API.
"""

import httpx
from typing import Optional, List

# Base URL for the FastAPI backend
API_BASE_URL = "http://127.0.0.1:8000/api/v1"


def _get_client() -> httpx.Client:
    """Create an HTTP client for API requests."""
    return httpx.Client(base_url=API_BASE_URL, timeout=10.0)


# ---- simple lookups --------------------------------------------------------

def get_categories():
    """Return all market categories sorted by name."""
    with _get_client() as client:
        response = client.get("/categories")
        response.raise_for_status()
        return response.json()


def get_markets(category_id=None):
    """Get markets, optionally filtering by category_id."""
    with _get_client() as client:
        params = {"category_id": category_id} if category_id is not None else {}
        response = client.get("/markets", params=params)
        response.raise_for_status()
        return response.json()


def get_individual_markets():
    """Only real country markets (skip the aggregate rows like 'Southeast Asia' total)."""
    with _get_client() as client:
        response = client.get("/markets/individual")
        response.raise_for_status()
        return response.json()


def get_year_range():
    """Returns {'min_year': ..., 'max_year': ...} from TimePeriod table."""
    with _get_client() as client:
        response = client.get("/year-range")
        response.raise_for_status()
        return response.json()


# ---- time series & aggregations -------------------------------------------

def get_arrivals_time_series(market_ids, start_year=None, end_year=None):
    """Monthly arrivals for the given market ids. Returns [] if no ids given."""
    if not market_ids:
        return []

    with _get_client() as client:
        params = {"market_ids": market_ids}
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year
        response = client.get("/arrivals/time-series", params=params)
        response.raise_for_status()
        return response.json()


def get_top_markets(n=10, start_year=None, end_year=None):
    """Top n markets ranked by total arrivals (excludes aggregate rows)."""
    with _get_client() as client:
        params = {"n": n}
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year
        response = client.get("/markets/top", params=params)
        response.raise_for_status()
        return response.json()


def get_seasonal_heatmap_data(market_id, start_year=None, end_year=None):
    """For the heatmap chart - returns year/month/arrival_count rows."""
    with _get_client() as client:
        params = {"market_id": market_id}
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year
        response = client.get("/arrivals/heatmap", params=params)
        response.raise_for_status()
        return response.json()


def get_category_share(start_year=None, end_year=None):
    """Totals per region for the pie chart."""
    with _get_client() as client:
        params = {}
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year
        response = client.get("/categories/share", params=params)
        response.raise_for_status()
        return response.json()


def get_yearly_totals(market_id=None):
    """Yearly sums. If market_id given, only that market; otherwise all individual markets."""
    with _get_client() as client:
        params = {}
        if market_id is not None:
            params["market_id"] = market_id
        response = client.get("/arrivals/yearly", params=params)
        response.raise_for_status()
        return response.json()


# ---- data explorer / detail view ------------------------------------------

def get_market_detail_table(market_ids, start_year=None, end_year=None):
    """Detailed rows for the DataTable in the explorer page."""
    if not market_ids:
        return []

    with _get_client() as client:
        params = {"market_ids": market_ids}
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year
        response = client.get("/markets/detail", params=params)
        response.raise_for_status()
        return response.json()


# ---- recovery comparison --------------------------------------------------

def get_recovery_comparison(market_ids, baseline_year=2019, comparison_year=2024):
    """
    Compares two years side by side for each market.
    Used for the covid recovery feature.
    """
    if not market_ids:
        return []

    with _get_client() as client:
        params = {
            "market_ids": market_ids,
            "baseline_year": baseline_year,
            "comparison_year": comparison_year
        }
        response = client.get("/recovery/comparison", params=params)
        response.raise_for_status()
        return response.json()