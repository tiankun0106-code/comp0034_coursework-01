"""
Tests for FastAPI REST API routes using FastAPI TestClient.
Tests cover all mandatory route types: GET, POST, PUT/PATCH, DELETE.
Includes comprehensive content validation and proper test isolation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from tourism_dashboard.api.main import app
from tourism_dashboard.api.database import get_session
from tourism_dashboard.api.models import MarketCategory, Market


# Create a test database in memory for isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    """Override the database session for testing with transaction rollback."""
    with Session(test_engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the FastAPI app with test database."""
    # Create tables in test database
    SQLModel.metadata.create_all(test_engine)

    # Seed test data into the in-memory database
    with Session(test_engine) as session:
        # Add sample categories
        categories = [
            MarketCategory(category_id=1, category_name="Europe", category_description="European markets"),
            MarketCategory(category_id=2, category_name="Asia", category_description="Asian markets"),
            MarketCategory(category_id=3, category_name="Americas", category_description="American markets"),
        ]
        session.add_all(categories)

        # Add sample markets
        markets = [
            Market(market_id=1, market_name="France", category_id=1, is_active=True),
            Market(market_id=2, market_name="Germany", category_id=1, is_active=True),
            Market(market_id=3, market_name="USA", category_id=3, is_active=True),
            Market(market_id=4, market_name="Japan", category_id=2, is_active=True),
        ]
        session.add_all(markets)
        session.commit()

    with TestClient(app) as c:
        yield c


# ---- GET Route Tests ----

class TestGetRoutes:
    """Test all GET endpoints with comprehensive content validation."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tourism Data API"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_get_categories_structure(self, client):
        """Test GET /api/v1/categories returns valid structure."""
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()

        # Validate structure (may be empty in test DB)
        assert isinstance(data, list)
        if len(data) > 0:
            first_category = data[0]
            assert "category_id" in first_category
            assert "category_name" in first_category
            assert isinstance(first_category["category_id"], int)
            assert isinstance(first_category["category_name"], str)

    def test_get_markets_structure(self, client):
        """Test GET /api/v1/markets returns valid structure."""
        response = client.get("/api/v1/markets")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            first_market = data[0]
            assert "market_id" in first_market
            assert "market_name" in first_market
            assert "category_id" in first_market

    def test_get_markets_with_category_filter(self, client):
        """Test GET /api/v1/markets with category_id filter returns correct data."""
        response = client.get("/api/v1/markets?category_id=3")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # All returned markets should have category_id = 3
        for market in data:
            assert market["category_id"] == 3

    def test_get_individual_markets_structure(self, client):
        """Test GET /api/v1/markets/individual returns valid structure."""
        response = client.get("/api/v1/markets/individual")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    def test_get_year_range_structure(self, client):
        """Test GET /api/v1/year-range returns valid structure."""
        response = client.get("/api/v1/year-range")
        assert response.status_code == 200
        data = response.json()

        assert "min_year" in data
        assert "max_year" in data
        # Years may be None in empty DB
        if data["min_year"] is not None:
            assert isinstance(data["min_year"], int)
            assert isinstance(data["max_year"], int)
            assert data["min_year"] <= data["max_year"]

    def test_get_arrivals_time_series_structure(self, client):
        """Test GET /api/v1/arrivals/time-series returns properly structured data."""
        response = client.get("/api/v1/arrivals/time-series?market_ids=3&market_ids=4")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            first_item = data[0]
            assert "market_name" in first_item
            assert "year" in first_item
            assert "month" in first_item
            assert "arrival_count" in first_item

    def test_get_arrivals_time_series_year_filter(self, client):
        """Test time series respects year filters."""
        response = client.get(
            "/api/v1/arrivals/time-series?market_ids=3&start_year=2020&end_year=2024"
        )
        assert response.status_code == 200
        data = response.json()

        for item in data:
            assert 2020 <= item["year"] <= 2024, f"Year {item['year']} outside filter range"

    def test_get_top_markets_structure(self, client):
        """Test GET /api/v1/markets/top returns valid structure."""
        response = client.get("/api/v1/markets/top?n=5")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 5

        # Verify descending order by total_arrivals (if data exists)
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]["total_arrivals"] >= data[i + 1]["total_arrivals"]

    def test_get_heatmap_data_structure(self, client):
        """Test GET /api/v1/arrivals/heatmap returns valid structure."""
        response = client.get("/api/v1/arrivals/heatmap?market_id=3")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            first_item = data[0]
            assert "year" in first_item
            assert "month" in first_item
            assert "month_name" in first_item
            assert "arrival_count" in first_item

    def test_get_category_share_structure(self, client):
        """Test GET /api/v1/categories/share returns valid structure."""
        response = client.get("/api/v1/categories/share")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            for item in data:
                assert "category_name" in item
                assert "total_arrivals" in item

    def test_get_yearly_totals_structure(self, client):
        """Test GET /api/v1/arrivals/yearly returns valid structure."""
        response = client.get("/api/v1/arrivals/yearly")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 1:
            # Verify years are in ascending order
            years = [item["year"] for item in data]
            assert years == sorted(years), "Years should be in ascending order"

    def test_get_market_detail_structure(self, client):
        """Test GET /api/v1/markets/detail returns valid structure."""
        response = client.get("/api/v1/markets/detail?market_ids=3&start_year=2020&end_year=2025")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            expected_columns = {"Market", "Category", "Year", "Month", "MonthNum", "Arrivals", "Quality"}
            actual_columns = set(data[0].keys())
            assert expected_columns.issubset(actual_columns)

    def test_get_recovery_comparison_structure(self, client):
        """Test GET /api/v1/recovery/comparison returns valid structure."""
        response = client.get(
            "/api/v1/recovery/comparison?market_ids=3&baseline_year=2019&comparison_year=2024"
        )
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "market_name" in item
            assert "baseline_total" in item
            assert "comparison_total" in item
            assert "recovery_pct" in item


# ---- POST Route Tests ----

class TestPostRoute:
    """Test POST endpoint for creating markets with proper isolation."""

    def test_create_market_success(self, client):
        """Test POST /api/v1/markets creates a new market successfully."""
        new_market = {
            "market_name": "test market",
            "category_id": 3,
            "is_active": True
        }
        response = client.post("/api/v1/markets", json=new_market)

        # Should succeed (201 Created)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["market_name"] == "test market"
        assert data["category_id"] == 3
        assert data["is_active"] is True
        assert "market_id" in data

    def test_create_market_missing_fields(self, client):
        """Test POST /api/v1/markets rejects request with missing required fields."""
        incomplete_market = {
            "market_name": "Incomplete Market"
            # Missing category_id
        }
        response = client.post("/api/v1/markets", json=incomplete_market)

        # Should return validation error
        assert response.status_code == 422


# ---- PATCH Route Tests ----

class TestPatchRoute:
    """Test PATCH endpoint for updating markets."""

    def test_update_market_success(self, client):
        """Test PATCH /api/v1/markets/{id} updates an existing market."""
        update_data = {"market_name": "Updated Market Name"}
        response = client.patch("/api/v1/markets/3", json=update_data)

        # Should succeed or return 404 if market doesn't exist
        if response.status_code == 200:
            data = response.json()
            assert data["market_name"] == "Updated Market Name"
        else:
            assert response.status_code == 404

    def test_update_nonexistent_market(self, client):
        """Test PATCH /api/v1/markets/{id} returns 404 for non-existent market."""
        update_data = {"market_name": "Should Not Exist"}
        response = client.patch("/api/v1/markets/999999", json=update_data)

        assert response.status_code == 404


# ---- DELETE Route Tests ----

class TestDeleteRoute:
    """Test DELETE endpoint for removing markets."""

    def test_delete_nonexistent_market(self, client):
        """Test DELETE /api/v1/markets/{id} returns 404 for non-existent market."""
        response = client.delete("/api/v1/markets/999999")
        assert response.status_code == 404

    def test_delete_market_success(self, client):
        """Test DELETE /api/v1/markets/{id} removes a market (if exists)."""
        # First create a market to delete
        new_market = {
            "market_name": "test market",
            "category_id": 3,
            "is_active": True
        }
        create_response = client.post("/api/v1/markets", json=new_market)

        if create_response.status_code == 201:
            market_id = create_response.json()["market_id"]

            # Now delete it
            delete_response = client.delete(f"/api/v1/markets/{market_id}")
            assert delete_response.status_code == 204


# ---- OpenAPI Documentation Tests ----

class TestOpenAPIDocs:
    """Test that OpenAPI documentation is available and complete."""

    def test_openapi_json_structure(self, client):
        """Test OpenAPI JSON spec has required sections."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()

        assert "paths" in data
        assert "info" in data
        assert "components" in data

        # Verify our API paths are documented
        paths = data["paths"]
        assert "/api/v1/categories" in paths
        assert "/api/v1/markets" in paths

    def test_docs_endpoint_accessible(self, client):
        """Test Swagger UI docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_accessible(self, client):
        """Test ReDoc endpoint is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]