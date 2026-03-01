"""
Tests for the layout module.
Check that all the layout builder functions return proper Dash components
and that the key elements (ids, options, etc.) are wired up correctly.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from tourism_dashboard.layout import (
    create_layout, create_navbar, create_global_filters,
    create_dashboard_section, create_explorer_section,
    create_recovery_section, _build_market_options,
    _build_category_options, _build_year_slider,
)


# ---- helper builders ----

def test_market_options_nonempty():
    opts = _build_market_options()
    assert len(opts) > 0


def test_market_options_structure():
    """Each option needs label + value for Dash dropdowns."""
    for opt in _build_market_options():
        assert "label" in opt and "value" in opt
        assert isinstance(opt["value"], int)


def test_category_options_no_aggregates():
    """Aggregate categories (id < 3) should be excluded."""
    for opt in _build_category_options():
        assert opt["value"] >= 3


def test_category_options_have_labels():
    opts = _build_category_options()
    assert len(opts) > 0
    for o in opts:
        assert len(o["label"]) > 0


def test_year_slider_returns_tuple():
    mn, mx = _build_year_slider()
    assert isinstance(mn, int) and isinstance(mx, int)
    assert mn < mx


# ---- full layout ----

def test_create_layout_returns_container():
    layout = create_layout()
    assert layout is not None
    # should be a dbc.Container
    assert isinstance(layout, dbc.Container)


def test_navbar_is_navbar():
    nav = create_navbar()
    assert isinstance(nav, dbc.Navbar)


def test_global_filters_is_card():
    filt = create_global_filters()
    assert isinstance(filt, dbc.Card)


def test_dashboard_section_has_id():
    section = create_dashboard_section()
    assert section.id == "dashboard"


def test_explorer_section_has_id():
    section = create_explorer_section()
    assert section.id == "explorer"


def test_recovery_section_has_id():
    section = create_recovery_section()
    assert section.id == "recovery"


# ---- check that key component ids exist in the layout tree ----

def _collect_ids(component):
    """Recursively collect all component ids from a Dash layout tree."""
    ids = set()
    if hasattr(component, "id") and component.id:
        ids.add(component.id)
    if hasattr(component, "children"):
        children = component.children
        if isinstance(children, (list, tuple)):
            for child in children:
                ids |= _collect_ids(child)
        elif children is not None:
            ids |= _collect_ids(children)
    return ids


def test_layout_contains_kpi_ids():
    layout = create_layout()
    ids = _collect_ids(layout)
    for kpi_id in ("kpi-total", "kpi-top-market", "kpi-markets", "kpi-years"):
        assert kpi_id in ids, f"Missing {kpi_id}"


def test_layout_contains_chart_ids():
    layout = create_layout()
    ids = _collect_ids(layout)
    for chart_id in ("yearly-trend-chart", "top-markets-chart",
                     "category-pie-chart", "seasonal-heatmap"):
        assert chart_id in ids, f"Missing {chart_id}"


def test_layout_contains_filter_ids():
    ids = _collect_ids(create_layout())
    assert "year-range-slider" in ids
    assert "category-filter" in ids


def test_layout_contains_explorer_ids():
    ids = _collect_ids(create_layout())
    for eid in ("explorer-market-select", "explorer-search-btn",
                "explorer-export-btn", "explorer-data-table"):
        assert eid in ids


def test_layout_contains_recovery_ids():
    ids = _collect_ids(create_layout())
    for rid in ("recovery-market-select", "recovery-analyze-btn",
                "recovery-baseline-year", "recovery-comparison-year"):
        assert rid in ids
