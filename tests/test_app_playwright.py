"""
tests/test_app_playwright.py – Playwright end-to-end tests for the Japanese Beetle Tracker.

Prerequisites
-------------
The app must be running locally before these tests execute.  Start it with:

    shiny run src/app.py --port 8000

Then run the tests with:

    pytest tests/test_app_playwright.py -v

The APP_URL environment variable can override the default localhost address:

    APP_URL=http://127.0.0.1:8000 pytest tests/test_app_playwright.py -v
"""

import os
import pytest
from playwright.sync_api import Page, expect

APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_app(page: Page) -> None:
    """Navigate to the app and wait until the sidebar is visible."""
    page.goto(APP_URL)
    page.wait_for_selector(".sidebar", timeout=30_000)
    page.wait_for_selector("#vb_total_obs .value-box-value", timeout=30_000)


def _get_total_obs(page: Page) -> int:
    """Read the current 'Total Observations' value box and return it as an int."""
    raw = page.locator("#vb_total_obs .value-box-value").inner_text()
    return int(raw.replace(",", "").strip())


def _get_first_recorded(page: Page) -> str:
    """Read the current 'First Recorded' value box and return it as a string."""
    return page.locator("#vb_first_recorded .value-box-value").inner_text().strip()


# ---------------------------------------------------------------------------
# Test 1 – Year-range filter narrows the observation count
# ---------------------------------------------------------------------------

class TestYearRangeFilter:
    """Behaviour: moving the year-range slider to a sub-range must reduce the
    total observation count shown in the 'Total Observations' value box.

    Why it matters: the slider is the primary temporal filter; if it has no
    effect the dashboard silently shows incorrect counts to every user."""

    def test_narrowing_year_range_reduces_count(self, page: Page):
        """Narrowing the year range must produce a smaller total-observation count
        than the full-range default."""
        _load_app(page)
        full_count = _get_total_obs(page)

        # Focus the left (min) thumb and move it right with Arrow keys.
        left_thumb = page.locator(".irs-handle.from").first
        left_thumb.click()
        for _ in range(30):
            page.keyboard.press("ArrowRight")

        page.wait_for_timeout(2_000)

        narrowed_count = _get_total_obs(page)
        assert narrowed_count < full_count, (
            f"Expected fewer observations after narrowing year range, "
            f"but got {narrowed_count} vs original {full_count}."
        )


# ---------------------------------------------------------------------------
# Test 2 – Reset button restores defaults
# ---------------------------------------------------------------------------

class TestResetButton:
    """Behaviour: clicking 'Reset Filters' must restore the total observation
    count to its original full-dataset value regardless of previous filter state.

    Why it matters: without a working reset, users who applied a filter have no
    reliable way to return to the full dataset view."""

    def test_reset_restores_full_count(self, page: Page):
        """After applying a basis-of-record filter and clicking Reset, the
        observation count must match the original unfiltered total."""
        _load_app(page)
        full_count = _get_total_obs(page)

        # Use radio buttons (plain HTML, no selectize complication)
        radios = page.locator("#basis_record input[type='radio']")
        radios.nth(1).click()
        page.wait_for_timeout(2_000)

        filtered_count = _get_total_obs(page)
        assert filtered_count != full_count, (
            "Basis-of-record filter had no effect — the reset test would be vacuous."
        )

        # Click Reset Filters
        page.locator("#reset_btn").click()
        page.wait_for_timeout(2_000)

        restored_count = _get_total_obs(page)
        assert restored_count == full_count, (
            f"Expected {full_count} observations after reset, got {restored_count}."
        )


# ---------------------------------------------------------------------------
# Test 3 – Year range change updates First Recorded value box
# ---------------------------------------------------------------------------

class TestFirstRecordedUpdates:
    """Behaviour: changing the year-range slider must update the 'First Recorded'
    value box to reflect the earliest year in the newly filtered dataset.

    Why it matters: the value box is a key summary statistic; if it does not
    react to the slider the user sees stale information alongside updated charts."""

    def test_first_recorded_updates_with_year_range(self, page: Page):
        """After advancing the lower year bound, 'First Recorded' must show a
        year greater than or equal to the original first-recorded year."""
        _load_app(page)
        original_first = _get_first_recorded(page)

        left_thumb = page.locator(".irs-handle.from").first
        left_thumb.click()
        for _ in range(20):
            page.keyboard.press("ArrowRight")

        page.wait_for_timeout(2_000)
        new_first = _get_first_recorded(page)

        if new_first != "N/A" and original_first != "N/A":
            assert int(new_first) >= int(original_first), (
                f"Expected First Recorded >= {original_first} after narrowing, "
                f"but got {new_first}."
            )


# ---------------------------------------------------------------------------
# Test 4 – Basis-of-record filter changes the total observation count
# ---------------------------------------------------------------------------

class TestBasisOfRecordFilter:
    """Behaviour: selecting a specific basis-of-record radio button must change
    the total observation count to match only that record type.

    Why it matters: the basis-of-record filter lets researchers isolate machine-
    detected vs human-observed records; an incorrect filter gives misleading totals."""

    def test_basis_filter_changes_count(self, page: Page):
        """Selecting any non-'All' basis-of-record option must produce a count
        different from the unfiltered total (assuming the dataset has >1 category)."""
        _load_app(page)
        full_count = _get_total_obs(page)

        radios = page.locator("#basis_record input[type='radio']")
        radios.nth(1).click()
        page.wait_for_timeout(2_000)

        filtered_count = _get_total_obs(page)
        assert filtered_count != full_count, (
            "Basis-of-record filter had no effect on the observation count."
        )


# ---------------------------------------------------------------------------
# Test 5 – Download CSV button is present and enabled on the AI Explorer tab
# ---------------------------------------------------------------------------

class TestDownloadCsvButton:
    """Behaviour: the 'Download CSV' button on the AI Explorer tab must be
    visible and not disabled so users can always export the current AI-filtered data.

    Why it matters: data download is an explicit feature; a broken or hidden
    button silently removes a capability users may depend on."""

    def test_download_button_visible_and_enabled(self, page: Page):
        """The Download CSV button must be present and not carry a 'disabled'
        attribute after navigating to the AI Explorer tab."""
        _load_app(page)

        # Target the nav link by text inside .nav-item
        page.locator(".nav-item a", has_text="AI Explorer").click()
        page.wait_for_timeout(2_000)

        btn = page.locator("#download_csv")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()