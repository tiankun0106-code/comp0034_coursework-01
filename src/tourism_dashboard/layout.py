"""
Dash layout - all the components and page structure.
Uses dash-bootstrap-components for the grid and styling.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table

from tourism_dashboard.data_access import (
    get_categories,
    get_individual_markets,
    get_year_range,
)


def _build_market_options():
    """Dropdown options list for the market selectors."""
    markets = get_individual_markets()
    return [
        {"label": f"{m['market_name']} ({m['category_name']})", "value": m["market_id"]}
        for m in markets
    ]


def _build_category_options():
    """Category dropdown options, skipping the aggregate rows."""
    categories = get_categories()
    return [
        {"label": c["category_name"], "value": c["category_id"]}
        for c in categories
        if c["category_id"] >= 3
    ]


def _build_year_slider():
    yr = get_year_range()
    return yr["min_year"], yr["max_year"]


def create_navbar():
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand(
                    [
                        html.I(className="bi bi-water me-2"),
                        "Tourism Recovery Analytics",
                    ],
                    className="fs-4 fw-bold",
                ),
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Dashboard", href="#dashboard", className="text-white")),
                        dbc.NavItem(dbc.NavLink("Data Explorer", href="#explorer", className="text-white")),
                        dbc.NavItem(dbc.NavLink("Recovery Analysis", href="#recovery", className="text-white")),
                    ],
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color="primary",
        dark=True,
        className="mb-4",
    )


def create_global_filters():
    min_year, max_year = _build_year_slider()

    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Year Range", className="fw-bold mb-1"),
                                dcc.RangeSlider(
                                    id="year-range-slider",
                                    min=min_year,
                                    max=max_year,
                                    value=[2015, max_year],
                                    marks={
                                        y: str(y)
                                        for y in range(min_year, max_year + 1, 5)
                                    },
                                    step=1,
                                    tooltip={"placement": "bottom", "always_visible": False},
                                ),
                            ],
                            md=8,
                        ),
                        dbc.Col(
                            [
                                html.Label("Region", className="fw-bold mb-1"),
                                dcc.Dropdown(
                                    id="category-filter",
                                    options=_build_category_options(),
                                    placeholder="All regions",
                                    clearable=True,
                                ),
                            ],
                            md=4,
                        ),
                    ],
                    className="align-items-end",
                ),
            ]
        ),
        className="mb-4 shadow-sm",
    )


def create_dashboard_section():
    return html.Div(
        id="dashboard",
        children=[
            html.H3("Dashboard Overview", className="mb-3 text-primary"),
            # kpi summary cards
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6("Total Arrivals", className="text-muted"),
                                    html.H3(id="kpi-total", children="—", className="fw-bold text-primary"),
                                ]
                            ),
                            className="shadow-sm text-center",
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6("Top Market", className="text-muted"),
                                    html.H3(id="kpi-top-market", children="—", className="fw-bold text-success"),
                                ]
                            ),
                            className="shadow-sm text-center",
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6("Markets Tracked", className="text-muted"),
                                    html.H3(id="kpi-markets", children="—", className="fw-bold text-info"),
                                ]
                            ),
                            className="shadow-sm text-center",
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6("Years of Data", className="text-muted"),
                                    html.H3(id="kpi-years", children="—", className="fw-bold text-warning"),
                                ]
                            ),
                            className="shadow-sm text-center",
                        ),
                        md=3,
                    ),
                ],
                className="mb-4",
            ),
            # row 1: trend + top markets
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Yearly Visitor Arrivals Trend"),
                                dbc.CardBody(dcc.Graph(id="yearly-trend-chart")),
                            ],
                            className="shadow-sm",
                        ),
                        md=7,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Top 10 Markets"),
                                dbc.CardBody(dcc.Graph(id="top-markets-chart")),
                            ],
                            className="shadow-sm",
                        ),
                        md=5,
                    ),
                ],
                className="mb-4",
            ),
            # row 2: pie + heatmap
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Market Share by Region"),
                                dbc.CardBody(dcc.Graph(id="category-pie-chart")),
                            ],
                            className="shadow-sm",
                        ),
                        md=5,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    dbc.Row(
                                        [
                                            dbc.Col(html.Span("Seasonal Heatmap"), md=6),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="heatmap-market-select",
                                                    options=_build_market_options()[:20],
                                                    value=1,
                                                    clearable=False,
                                                    style={"fontSize": "0.85rem"},
                                                ),
                                                md=6,
                                            ),
                                        ],
                                        align="center",
                                    )
                                ),
                                dbc.CardBody(dcc.Graph(id="seasonal-heatmap")),
                            ],
                            className="shadow-sm",
                        ),
                        md=7,
                    ),
                ],
                className="mb-4",
            ),
        ],
    )


def create_explorer_section():
    """The data explorer page - filter form + chart + table."""
    return html.Div(
        id="explorer",
        children=[
            html.H3("Data Explorer", className="mb-3 text-primary"),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Filter & Search", className="mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Select Markets", className="fw-bold mb-1"),
                                        dcc.Dropdown(
                                            id="explorer-market-select",
                                            options=_build_market_options(),
                                            multi=True,
                                            placeholder="Choose one or more markets...",
                                        ),
                                    ],
                                    md=6,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Year From", className="fw-bold mb-1"),
                                        dbc.Input(
                                            id="explorer-year-from",
                                            type="number",
                                            min=1978,
                                            max=2025,
                                            value=2020,
                                        ),
                                    ],
                                    md=3,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Year To", className="fw-bold mb-1"),
                                        dbc.Input(
                                            id="explorer-year-to",
                                            type="number",
                                            min=1978,
                                            max=2025,
                                            value=2025,
                                        ),
                                    ],
                                    md=3,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Button(
                            "Search",
                            id="explorer-search-btn",
                            color="primary",
                            className="me-2",
                        ),
                        dbc.Button(
                            "Export JSON",
                            id="explorer-export-btn",
                            color="secondary",
                            outline=True,
                        ),
                        dcc.Download(id="explorer-download"),
                    ]
                ),
                className="shadow-sm mb-4",
            ),
            # chart
            dbc.Card(
                [
                    dbc.CardHeader("Monthly Arrivals Comparison"),
                    dbc.CardBody(dcc.Graph(id="explorer-time-series")),
                ],
                className="shadow-sm mb-4",
            ),
            # table with sorting/filtering
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(html.Span("Detailed Data Table"), md=8),
                                dbc.Col(
                                    html.Span(id="table-row-count", className="text-muted"),
                                    md=4,
                                    className="text-end",
                                ),
                            ]
                        )
                    ),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id="explorer-data-table",
                            columns=[
                                {"name": "Market", "id": "Market"},
                                {"name": "Category", "id": "Category"},
                                {"name": "Year", "id": "Year"},
                                {"name": "Month", "id": "Month"},
                                {"name": "Arrivals", "id": "Arrivals", "type": "numeric",
                                 "format": {"specifier": ","}},
                                {"name": "Quality", "id": "Quality"},
                            ],
                            page_size=15,
                            sort_action="native",
                            filter_action="native",
                            style_table={"overflowX": "auto"},
                            style_header={
                                "backgroundColor": "#0d6efd",
                                "color": "white",
                                "fontWeight": "bold",
                            },
                            style_cell={
                                "textAlign": "left",
                                "padding": "8px",
                                "fontSize": "0.9rem",
                            },
                            style_data_conditional=[
                                {
                                    "if": {"row_index": "odd"},
                                    "backgroundColor": "#f8f9fa",
                                },
                                {
                                    "if": {
                                        "filter_query": "{Quality} = MISSING",
                                    },
                                    "backgroundColor": "#fff3cd",
                                },
                            ],
                        )
                    ),
                ],
                className="shadow-sm mb-4",
            ),
        ],
    )


def create_recovery_section():
    """COVID recovery comparison - the 'beyond dashboard' feature."""
    return html.Div(
        id="recovery",
        children=[
            html.H3("COVID Recovery Analysis", className="mb-3 text-primary"),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Compare Pre-COVID vs Post-COVID", className="mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Select Markets", className="fw-bold mb-1"),
                                        dcc.Dropdown(
                                            id="recovery-market-select",
                                            options=_build_market_options(),
                                            multi=True,
                                            value=[],
                                            placeholder="Choose markets to compare...",
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Baseline Year", className="fw-bold mb-1"),
                                        dbc.Input(
                                            id="recovery-baseline-year",
                                            type="number",
                                            value=2019,
                                        ),
                                    ],
                                    md=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Comparison Year", className="fw-bold mb-1"),
                                        dbc.Input(
                                            id="recovery-comparison-year",
                                            type="number",
                                            value=2024,
                                        ),
                                    ],
                                    md=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("\u00A0", className="d-block mb-1"),
                                        dbc.Button(
                                            "Analyze",
                                            id="recovery-analyze-btn",
                                            color="success",
                                            className="w-100",
                                        ),
                                    ],
                                    md=2,
                                ),
                            ],
                        ),
                    ]
                ),
                className="shadow-sm mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Recovery Rate (%)"),
                                dbc.CardBody(dcc.Graph(id="recovery-bar-chart")),
                            ],
                            className="shadow-sm",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Arrivals Comparison"),
                                dbc.CardBody(dcc.Graph(id="recovery-grouped-bar")),
                            ],
                            className="shadow-sm",
                        ),
                        md=6,
                    ),
                ],
                className="mb-4",
            ),
        ],
    )


def create_layout():
    """Assemble the full page layout."""
    return dbc.Container(
        [
            create_navbar(),
            create_global_filters(),
            create_dashboard_section(),
            html.Hr(),
            create_explorer_section(),
            html.Hr(),
            create_recovery_section(),
            # footer with data attribution
            html.Footer(
                dbc.Container(
                    html.P(
                        [
                            "Tourism Recovery Analytics Dashboard | ",
                            "Data: International Visitor Arrivals by Sea (Monthly) | ",
                            html.A(
                                "Open Government Licence v3",
                                href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                                target="_blank",
                            ),
                        ],
                        className="text-muted text-center py-3",
                    )
                ),
                className="mt-4 bg-light",
            ),
        ],
        fluid=True,
        className="px-4",
    )
