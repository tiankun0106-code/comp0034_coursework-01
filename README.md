# Tourism Recovery Analytics Dashboard

COMP0034 Coursework 1 & 2 - Full-stack web application for analyzing international visitor arrivals by sea.

## Project Overview

This project consists of two integrated applications:

### Frontend (Coursework 1)
A Dash web application providing an interactive analytics dashboard for exploring international visitor arrival data, with features including:

- **Dashboard**: KPI cards, yearly trend charts, top markets, regional market share, and seasonal heatmaps
- **Data Explorer**: Multi-market selection, year filtering, monthly time series comparison, sortable/filterable data table, and JSON export
- **COVID Recovery Analysis**: Compare pre-COVID baseline with post-COVID data, recovery rate visualization

### Backend (Coursework 2)
A FastAPI REST API backend that serves as the data layer for the frontend application:

- **REST API**: 14 endpoints covering GET, POST, PATCH, DELETE operations
- **ORM**: SQLModel-based database models with Pydantic validation
- **OpenAPI Documentation**: Auto-generated Swagger UI and ReDoc documentation
- **Testing**: Comprehensive test suite using FastAPI TestClient with in-memory database isolation

## Project Structure

```
comp0034-coursework/
├── src/
│   └── tourism_dashboard/
│       ├── __init__.py
│       ├── app.py              # Main Dash application (frontend entry point)
│       ├── layout.py           # Dashboard layout and components
│       ├── callbacks.py        # Interactive callback functions
│       ├── data_access.py      # HTTP client for REST API calls
│       └── api/                # FastAPI backend (Coursework 2)
│           ├── __init__.py
│           ├── main.py         # FastAPI application entry point
│           ├── database.py     # Database connection and session management
│           ├── models.py       # SQLModel ORM models
│           ├── schemas.py      # Pydantic request/response schemas
│           └── routes.py       # REST API route definitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_data_access.py     # Unit/integration tests for data layer
│   ├── test_browser.py         # Selenium browser tests
│   └── test_api_routes.py      # FastAPI route tests
├── data/
│   └── international_visitor_arrivals.db
├── alembic/                    # Database migration scripts
│   ├── env.py
│   └── versions/
├── alembic.ini                 # Alembic configuration
├── pyproject.toml
├── submission.yml
└── README.md
```

## Installation

### Prerequisites
- Python 3.12 or higher
- pip package manager
- Google Chrome (for browser tests)

### Setup

1. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Install the package**:
   ```bash
   pip install -e .
   ```

3. **Install dev dependencies** (for testing):
   ```bash
   pip install -e ".[dev]"
   ```

## Running the Application

### Start the Backend (FastAPI)

```bash
# Terminal 1: Start the FastAPI backend
fastapi dev src/tourism_dashboard/api/main.py
```

The API will be available at http://127.0.0.1:8000 with auto-generated documentation at http://127.0.0.1:8000/docs

### Start the Frontend (Dash)

```bash
# Terminal 2: Start the Dash frontend
python src/tourism_dashboard/app.py
```

Then open http://127.0.0.1:8050 in your browser to access the dashboard.

## Running Tests

### Run all tests:
```bash
python -m pytest
```

### Run data access tests only:
```bash
python -m pytest tests/test_data_access.py -v
```

### Run browser tests only:
```bash
python -m pytest tests/test_browser.py -v
```

### Run with coverage:
```bash
python -m pytest --cov=src --cov-report=html --cov-report=term
```

## Data Source

International Visitor Arrivals By Inbound Tourism Markets (Sea), Monthly.

Licensed under the [Open Government Licence v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
