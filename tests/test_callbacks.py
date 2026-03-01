"""
Unit tests for callback helpers and the app's callback registration.
These don't need a browser - they test the logic directly.
"""

import plotly.graph_objects as go
from tourism_dashboard.callbacks import _blank_fig, MONTH_ORDER, _MARGINS
from tourism_dashboard.app import create_app


# ---- _blank_fig helper ----

def test_blank_fig_returns_figure():
    fig = _blank_fig()
    assert isinstance(fig, go.Figure)


def test_blank_fig_default_message():
    fig = _blank_fig()
    annotations = fig.layout.annotations
    assert len(annotations) == 1
    assert annotations[0].text == "No data"


def test_blank_fig_custom_message():
    fig = _blank_fig("Something went wrong")
    assert fig.layout.annotations[0].text == "Something went wrong"


def test_blank_fig_axes_hidden():
    fig = _blank_fig()
    assert fig.layout.xaxis.visible is False
    assert fig.layout.yaxis.visible is False


# ---- constants ----

def test_month_order_has_12():
    assert len(MONTH_ORDER) == 12


def test_month_order_starts_jan():
    assert MONTH_ORDER[0] == "Jan"
    assert MONTH_ORDER[11] == "Dec"


def test_margins_dict_keys():
    assert set(_MARGINS.keys()) == {"l", "r", "t", "b"}
    for v in _MARGINS.values():
        assert isinstance(v, int)


# ---- app + callback registration ----

def test_app_creates_successfully():
    app = create_app()
    assert app is not None


def test_app_has_title():
    app = create_app()
    assert app.title == "Tourism Recovery Analytics"


def test_app_layout_not_none():
    app = create_app()
    assert app.layout is not None


def test_callbacks_registered():
    """After create_app, the callback map should have entries."""
    app = create_app()
    # Dash stores callbacks internally - just check it's not empty
    assert len(app.callback_map) > 0


def test_suppress_callback_exceptions():
    app = create_app()
    assert app.config.suppress_callback_exceptions is True
