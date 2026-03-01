"""
All the Dash callbacks live here.
Separated from layout so the app.py stays clean.
"""

import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash import Input, Output, State, no_update, dcc

from tourism_dashboard import data_access as da


# small helper so I don't repeat the "no data" figure everywhere
def _blank_fig(msg="No data"):
    fig = go.Figure()
    fig.update_layout(
        xaxis={"visible": False}, yaxis={"visible": False},
        annotations=[{
            "text": msg, "xref": "paper", "yref": "paper",
            "x": 0.5, "y": 0.5, "showarrow": False,
            "font": {"size": 16, "color": "gray"},
        }],
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# keep a compact margin dict i reuse a lot
_MARGINS = dict(l=20, r=20, t=10, b=20)


def register_callbacks(app):
    """Wire up all the callbacks to the app."""

    # ---------- KPI cards ----------
    @app.callback(
        [Output("kpi-total", "children"),
         Output("kpi-top-market", "children"),
         Output("kpi-markets", "children"),
         Output("kpi-years", "children")],
        [Input("year-range-slider", "value"),
         Input("category-filter", "value")],
    )
    def update_kpis(year_range, category_id):
        sy, ey = year_range
        top = da.get_top_markets(n=1, start_year=sy, end_year=ey)
        all_mkts = da.get_individual_markets()

        # filter by category if user selected one
        if category_id:
            cats = da.get_categories()
            cat_name = next((c["category_name"] for c in cats
                             if c["category_id"] == category_id), "")
            all_mkts = [m for m in all_mkts if m.get("category_name") == cat_name]

        # total arrivals across all individual markets
        total_data = da.get_top_markets(n=100, start_year=sy, end_year=ey)
        total = sum(m["total_arrivals"] for m in total_data)

        top_name = top[0]["market_name"] if top else "N/A"
        return f"{total:,}", top_name, str(len(all_mkts)), f"{sy}\u2013{ey}"

    # ---------- yearly trend line chart ----------
    @app.callback(
        Output("yearly-trend-chart", "figure"),
        [Input("year-range-slider", "value"),
         Input("category-filter", "value")],
    )
    def update_yearly_trend(year_range, _cat):
        sy, ey = year_range
        data = da.get_yearly_totals()
        df = pd.DataFrame(data)
        if df.empty:
            return _blank_fig("No data available")

        df = df[(df["year"] >= sy) & (df["year"] <= ey)]
        fig = px.line(df, x="year", y="total_arrivals", markers=True,
                      labels={"year": "Year", "total_arrivals": "Total Arrivals"})
        fig.update_layout(margin=_MARGINS, hovermode="x unified", yaxis_tickformat=",")
        fig.update_traces(line_color="#0d6efd", line_width=2.5, marker_size=6)
        return fig

    # ---------- top 10 markets bar ----------
    @app.callback(
        Output("top-markets-chart", "figure"),
        [Input("year-range-slider", "value"),
         Input("category-filter", "value")],
    )
    def update_top_markets(year_range, _cat):
        sy, ey = year_range
        data = da.get_top_markets(n=10, start_year=sy, end_year=ey)
        if not data:
            return _blank_fig()

        df = pd.DataFrame(data)
        fig = px.bar(df, x="total_arrivals", y="market_name", orientation="h",
                     color="category_name",
                     labels={"total_arrivals": "Total Arrivals",
                             "market_name": "", "category_name": "Region"})
        fig.update_layout(
            margin=_MARGINS, yaxis={"autorange": "reversed"},
            xaxis_tickformat=",",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            height=380)
        return fig

    # ---------- pie chart by region ----------
    @app.callback(
        Output("category-pie-chart", "figure"),
        Input("year-range-slider", "value"),
    )
    def update_pie(year_range):
        sy, ey = year_range
        data = da.get_category_share(start_year=sy, end_year=ey)
        if not data:
            return _blank_fig()
        df = pd.DataFrame(data)
        fig = px.pie(df, values="total_arrivals", names="category_name",
                     hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(margin=_MARGINS, legend_font_size=10)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        return fig

    # ---------- seasonal heatmap (this one was tricky to get right) ----------
    @app.callback(
        Output("seasonal-heatmap", "figure"),
        [Input("year-range-slider", "value"),
         Input("heatmap-market-select", "value")],
    )
    def update_heatmap(year_range, market_id):
        if not market_id:
            return _blank_fig("Select a market")

        sy, ey = year_range
        data = da.get_seasonal_heatmap_data(market_id, start_year=sy, end_year=ey)
        if not data:
            return _blank_fig("No data for this market")

        df = pd.DataFrame(data)

        # pivot: rows=month, cols=year, values=arrivals
        pivot = df.pivot_table(index="month_name", columns="year",
                               values="arrival_count", aggfunc="sum")
        # had a bug here where months showed alphabetically - need to force the order
        pivot = pivot.reindex([m for m in MONTH_ORDER if m in pivot.index])

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[str(c) for c in pivot.columns],
            y=pivot.index,
            colorscale="YlOrRd",
            hovertemplate="Year: %{x}<br>Month: %{y}<br>Arrivals: %{z:,}<extra></extra>",
        ))
        fig.update_layout(margin=_MARGINS, xaxis_title="Year",
                          yaxis_title="Month", height=380)
        return fig

    # ---------- explorer: search & table ----------
    @app.callback(
        [Output("explorer-time-series", "figure"),
         Output("explorer-data-table", "data"),
         Output("table-row-count", "children")],
        Input("explorer-search-btn", "n_clicks"),
        [State("explorer-market-select", "value"),
         State("explorer-year-from", "value"),
         State("explorer-year-to", "value")],
        prevent_initial_call=True,
    )
    def update_explorer(n_clicks, market_ids, yr_from, yr_to):
        if not market_ids:
            return _blank_fig("Select at least one market"), [], "0 rows"

        ts_data = da.get_arrivals_time_series(market_ids, start_year=yr_from, end_year=yr_to)
        if not ts_data:
            return _blank_fig("No data found"), [], "0 rows"

        df = pd.DataFrame(ts_data)
        # build a proper date column for the x-axis
        df["date"] = pd.to_datetime(
            df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
        )

        fig = px.line(df, x="date", y="arrival_count", color="market_name",
                      labels={"date": "Date", "arrival_count": "Arrivals",
                              "market_name": "Market"})
        fig.update_layout(margin=_MARGINS, hovermode="x unified", yaxis_tickformat=",")

        table_data = da.get_market_detail_table(market_ids, start_year=yr_from, end_year=yr_to)
        return fig, table_data, f"{len(table_data):,} rows"

    # ---------- explorer: json export ----------
    @app.callback(
        Output("explorer-download", "data"),
        Input("explorer-export-btn", "n_clicks"),
        [State("explorer-market-select", "value"),
         State("explorer-year-from", "value"),
         State("explorer-year-to", "value")],
        prevent_initial_call=True,
    )
    def export_json(n_clicks, market_ids, yr_from, yr_to):
        if not market_ids:
            return no_update
        rows = da.get_market_detail_table(market_ids, start_year=yr_from, end_year=yr_to)
        return dcc.send_string(
            json.dumps(rows, indent=2, default=str),
            filename="tourism_data_export.json",
        )

    # ---------- recovery comparison ----------
    @app.callback(
        [Output("recovery-bar-chart", "figure"),
         Output("recovery-grouped-bar", "figure")],
        Input("recovery-analyze-btn", "n_clicks"),
        [State("recovery-market-select", "value"),
         State("recovery-baseline-year", "value"),
         State("recovery-comparison-year", "value")],
        prevent_initial_call=True,
    )
    def update_recovery(n_clicks, market_ids, base_yr, comp_yr):
        if not market_ids:
            empty = _blank_fig("Select markets to compare")
            return empty, empty

        data = da.get_recovery_comparison(market_ids, base_yr, comp_yr)
        if not data:
            empty = _blank_fig("No data found")
            return empty, empty

        df = pd.DataFrame(data)

        # fig 1 - recovery % with a 100% reference line
        fig1 = px.bar(df, x="market_name", y="recovery_pct", color="recovery_pct",
                      color_continuous_scale=["#dc3545", "#ffc107", "#198754"],
                      labels={"market_name": "Market", "recovery_pct": "Recovery %"})
        fig1.add_hline(y=100, line_dash="dash", line_color="gray",
                       annotation_text="100% Recovery")
        fig1.update_layout(margin=_MARGINS, coloraxis_showscale=False)

        # fig 2 - grouped bars baseline vs comparison
        melted = df.melt(id_vars=["market_name"],
                         value_vars=["baseline_total", "comparison_total"],
                         var_name="Period", value_name="Total Arrivals")
        melted["Period"] = melted["Period"].replace({
            "baseline_total": str(base_yr), "comparison_total": str(comp_yr)
        })
        fig2 = px.bar(melted, x="market_name", y="Total Arrivals",
                      color="Period", barmode="group",
                      labels={"market_name": "Market"},
                      color_discrete_map={str(base_yr): "#6c757d",
                                          str(comp_yr): "#0d6efd"})
        fig2.update_layout(margin=_MARGINS, yaxis_tickformat=",")

        return fig1, fig2
