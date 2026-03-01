"""
Main entry point for the Tourism Dashboard app.
Run: python src/dashboard/app.py
"""

import dash
import dash_bootstrap_components as dbc
from tourism_dashboard.layout import create_layout
from tourism_dashboard.callbacks import register_callbacks


def create_app():
    """App factory - sets up Dash with bootstrap theme, layout and callbacks."""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
        title="Tourism Recovery Analytics",
        suppress_callback_exceptions=True,
    )
    app.layout = create_layout()
    register_callbacks(app)
    return app


app = create_app()
server = app.server  # needed if deploying with gunicorn etc

if __name__ == "__main__":
    app.run(debug=True, port=8050)
