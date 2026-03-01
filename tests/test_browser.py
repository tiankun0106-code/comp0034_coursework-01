"""
Selenium browser tests for the dashboard.
These are end-to-end tests - they spin up the real app and poke at it
through a headless Chrome browser.

Requires: chrome + chromedriver on the system.
If not available, all tests in this file get skipped automatically.
"""

import pytest
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

pytestmark = pytest.mark.skipif(not HAS_SELENIUM, reason="selenium not installed")


@pytest.fixture(scope="module")
def browser(dash_server):
    """Headless chrome fixture, shared across this module."""
    # try auto-installing chromedriver if the package is there
    try:
        import chromedriver_autoinstaller
        chromedriver_autoinstaller.install()
    except ImportError:
        pass  # hope it's on PATH already

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=opts)
    except Exception:
        pytest.skip("couldn't start Chrome - skipping browser tests")
        return

    driver.get(dash_server)
    time.sleep(3)  # give Dash a moment to render everything
    yield driver
    driver.quit()


# ---- basic page structure ----

def test_page_title(browser):
    assert "Tourism" in browser.title


def test_navbar_shows_up(browser):
    navbars = browser.find_elements(By.CLASS_NAME, "navbar")
    assert len(navbars) > 0


def test_navbar_brand(browser):
    brand = browser.find_element(By.CLASS_NAME, "navbar-brand")
    assert "Tourism Recovery Analytics" in brand.text


def test_all_sections_rendered(browser):
    """All three main sections should be in the DOM."""
    for section_id in ("dashboard", "explorer", "recovery"):
        el = browser.find_element(By.ID, section_id)
        assert el is not None


# ---- KPI cards ----

def test_kpi_total_updates(browser):
    """The total arrivals KPI should show an actual number after callbacks fire."""
    wait = WebDriverWait(browser, 10)
    kpi = wait.until(EC.presence_of_element_located((By.ID, "kpi-total")))
    time.sleep(2)  # callbacks need a sec
    assert kpi.text not in ("", None)


def test_kpi_top_market(browser):
    text = browser.find_element(By.ID, "kpi-top-market").text
    # should be a real market name, not the placeholder dash
    assert text != "" and text != "\u2014"


def test_kpi_market_count(browser):
    text = browser.find_element(By.ID, "kpi-markets").text
    assert text.isdigit() and int(text) > 0


# ---- charts ----

def _chart_has_svg(browser, chart_id):
    """Check that a plotly chart rendered at least one svg element."""
    div = browser.find_element(By.ID, chart_id)
    svgs = div.find_elements(By.TAG_NAME, "svg")
    return len(svgs) > 0


def test_trend_chart(browser):
    time.sleep(2)
    assert _chart_has_svg(browser, "yearly-trend-chart")


def test_top_markets_chart(browser):
    assert _chart_has_svg(browser, "top-markets-chart")


def test_pie_chart(browser):
    assert _chart_has_svg(browser, "category-pie-chart")


def test_heatmap(browser):
    assert _chart_has_svg(browser, "seasonal-heatmap")


# ---- global filters ----

def test_year_slider_visible(browser):
    slider = browser.find_element(By.ID, "year-range-slider")
    assert slider.is_displayed()


def test_category_dropdown_visible(browser):
    dd = browser.find_element(By.ID, "category-filter")
    assert dd.is_displayed()


# ---- data explorer section ----

def test_explorer_market_dropdown(browser):
    assert browser.find_element(By.ID, "explorer-market-select") is not None


def test_explorer_search_btn(browser):
    btn = browser.find_element(By.ID, "explorer-search-btn")
    assert btn.is_enabled()


def test_explorer_export_btn(browser):
    assert browser.find_element(By.ID, "explorer-export-btn") is not None


def test_explorer_data_table(browser):
    assert browser.find_element(By.ID, "explorer-data-table") is not None


# ---- recovery section ----

def test_recovery_dropdown(browser):
    assert browser.find_element(By.ID, "recovery-market-select") is not None


def test_recovery_analyze_btn(browser):
    btn = browser.find_element(By.ID, "recovery-analyze-btn")
    assert btn.is_enabled()


def test_recovery_default_years(browser):
    """Check that the baseline/comparison inputs default to 2019 and 2024."""
    base = browser.find_element(By.ID, "recovery-baseline-year")
    comp = browser.find_element(By.ID, "recovery-comparison-year")
    assert base.get_attribute("value") == "2019"
    assert comp.get_attribute("value") == "2024"
