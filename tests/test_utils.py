"""
tests/test_utils.py – Unit tests for the pure helper functions in utils.py.

Run with:
    pytest tests/test_utils.py -v

Each test includes a one-sentence description (in the docstring) explaining
what behaviour is verified and why it matters for the dashboard.
"""

import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    apply_filters,
    compute_first_recorded,
    compute_status,
    prepare_timeseries,
    prepare_basis_counts,
    prepare_rights_holder,
    prepare_monthly,
)


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Minimal beetle DataFrame that exercises every column used by utils."""
    return pd.DataFrame(
        {
            "year": [2000, 2000, 2005, 2010, 2010, 2015],
            "countryCode": ["US", "CA", "US", "US", "CA", "US"],
            "basisOfRecord": [
                "HUMAN_OBSERVATION",
                "HUMAN_OBSERVATION",
                "PRESERVED_SPECIMEN",
                "HUMAN_OBSERVATION",
                "PRESERVED_SPECIMEN",
                "HUMAN_OBSERVATION",
            ],
            "rightsHolder": ["Alice", "Bob", "Alice", "Carol", "Alice", "Bob"],
            "eventDate": [
                "2000-06-15",
                "2000-07-20",
                "2005-08-01",
                "2010-03-10",
                "2010-09-25",
                "2015-05-05",
            ],
            "decimalLatitude": [45.0, 50.0, 40.0, 38.0, 49.0, 42.0],
            "decimalLongitude": [-75.0, -80.0, -90.0, -95.0, -85.0, -88.0],
            "stateProvince": ["NY", "ON", "IL", "MO", "ON", "IL"],
        }
    )


# ---------------------------------------------------------------------------
# apply_filters
# ---------------------------------------------------------------------------

class TestApplyFilters:
    def test_year_range_reduces_rows(self, sample_df):
        """Filtering to a sub-range of years must return only rows within that range,
        ensuring the slider correctly narrows the dataset shown in every chart and map."""
        result = apply_filters(sample_df, 2000, 2005)
        assert set(result["year"].unique()) == {2000, 2005}
        assert len(result) == 3

    def test_region_filter(self, sample_df):
        """Selecting a specific country code must exclude all other countries,
        so the dashboard accurately reflects observations for that region only."""
        result = apply_filters(sample_df, 2000, 2015, region="CA")
        assert all(result["countryCode"] == "CA")
        assert len(result) == 2

    def test_basis_of_record_filter(self, sample_df):
        """Filtering by basis of record must keep only rows with that exact category,
        allowing users to isolate observation types like 'PRESERVED_SPECIMEN'."""
        result = apply_filters(
            sample_df, 2000, 2015, basis_of_record="PRESERVED_SPECIMEN"
        )
        assert all(result["basisOfRecord"] == "PRESERVED_SPECIMEN")
        assert len(result) == 2

    def test_all_filters_combined(self, sample_df):
        """Combining year, region, and basis filters must intersect all three conditions,
        confirming the filtering logic is conjunctive (AND) and not additive (OR)."""
        result = apply_filters(
            sample_df, 2000, 2005, region="US", basis_of_record="HUMAN_OBSERVATION"
        )
        assert len(result) == 1
        assert result.iloc[0]["year"] == 2000
        assert result.iloc[0]["countryCode"] == "US"

    def test_all_filters_all_returns_full_range(self, sample_df):
        """Passing 'All' for region and basis must return all rows within the year bounds,
        matching the dashboard's default 'no filter applied' state."""
        result = apply_filters(sample_df, 2000, 2015)
        assert len(result) == len(sample_df)

    def test_empty_result_when_no_match(self, sample_df):
        """A filter combination that matches no rows must return an empty DataFrame,
        so value boxes and charts gracefully handle the empty state."""
        result = apply_filters(sample_df, 2000, 2015, region="DE")
        assert result.empty


# ---------------------------------------------------------------------------
# compute_first_recorded
# ---------------------------------------------------------------------------

class TestComputeFirstRecorded:
    def test_returns_minimum_year(self, sample_df):
        """The first-recorded value box must show the earliest year in the filtered data,
        giving users an accurate start date for beetle presence in the selected region."""
        assert compute_first_recorded(sample_df) == "2000"

    def test_returns_na_for_empty_df(self):
        """An empty DataFrame must produce 'N/A', preventing a crash when filters
        eliminate all rows and the value box has nothing to display."""
        empty = pd.DataFrame({"year": pd.Series([], dtype=float)})
        assert compute_first_recorded(empty) == "N/A"

    def test_returns_na_when_all_years_nan(self):
        """All-NaN years must produce 'N/A', handling datasets where year is missing
        for every observation in the current filter selection."""
        df = pd.DataFrame({"year": [float("nan"), float("nan")]})
        assert compute_first_recorded(df) == "N/A"

    def test_ignores_nan_years(self, sample_df):
        """NaN year values must be ignored when computing the minimum, so a handful of
        records with missing years do not corrupt the first-recorded display."""
        df_with_nan = sample_df.copy()
        df_with_nan.loc[0, "year"] = float("nan")
        # minimum among non-NaN is 2000 (row 1) → still "2000"
        assert compute_first_recorded(df_with_nan) == "2000"


# ---------------------------------------------------------------------------
# compute_status
# ---------------------------------------------------------------------------

class TestComputeStatus:
    def test_present_when_year_matches(self, sample_df):
        """Status must be 'Present' when at least one observation falls in the slider's
        max year, correctly indicating current beetle presence in the selected area."""
        assert compute_status(sample_df, 2015) == "Present"

    def test_not_detected_when_year_absent(self, sample_df):
        """Status must be 'Not Detected' when no observation matches the slider's max
        year, accurately signalling absence for that reference year."""
        assert compute_status(sample_df, 2020) == "Not Detected"

    def test_not_detected_for_empty_df(self):
        """An empty filtered DataFrame must always return 'Not Detected', preventing
        a false positive when all filters eliminate every row."""
        empty = pd.DataFrame({"year": pd.Series([], dtype=float)})
        assert compute_status(empty, 2015) == "Not Detected"


# ---------------------------------------------------------------------------
# prepare_timeseries
# ---------------------------------------------------------------------------

class TestPrepareTimeseries:
    def test_columns_present(self, sample_df):
        """The timeseries helper must return a DataFrame with exactly 'year' and 'count'
        columns, which the Altair line chart encodes directly."""
        result = prepare_timeseries(sample_df)
        assert list(result.columns) == ["year", "count"]

    def test_counts_are_correct(self, sample_df):
        """Each year's count must match the actual number of rows for that year in the
        filtered data, so the time-series chart reflects reality."""
        result = prepare_timeseries(sample_df)
        counts = result.set_index("year")["count"].to_dict()
        assert counts[2000] == 2
        assert counts[2005] == 1
        assert counts[2010] == 2
        assert counts[2015] == 1

    def test_empty_df_returns_empty(self):
        """An empty input must produce an empty output DataFrame, allowing the Altair
        chart to render a blank canvas rather than raising an exception."""
        empty = pd.DataFrame({"year": pd.Series([], dtype=int)})
        result = prepare_timeseries(empty)
        assert result.empty


# ---------------------------------------------------------------------------
# prepare_basis_counts
# ---------------------------------------------------------------------------

class TestPrepareBasisCounts:
    def test_columns_present(self, sample_df):
        """The basis-counts helper must return 'basisOfRecord' and 'count' columns,
        matching the field names the Altair pie chart encodes."""
        result = prepare_basis_counts(sample_df)
        assert list(result.columns) == ["basisOfRecord", "count"]

    def test_counts_correct(self, sample_df):
        """HUMAN_OBSERVATION must be counted as 4 and PRESERVED_SPECIMEN as 2,
        so the pie chart correctly shows the proportion of each record type."""
        result = prepare_basis_counts(sample_df)
        counts = result.set_index("basisOfRecord")["count"].to_dict()
        assert counts["HUMAN_OBSERVATION"] == 4
        assert counts["PRESERVED_SPECIMEN"] == 2

    def test_drops_nan(self):
        """NaN basisOfRecord values must be excluded from the count, preventing an
        'Unknown' slice that would mislead users about record-type distribution."""
        df = pd.DataFrame({"basisOfRecord": ["A", None, "A", None]})
        result = prepare_basis_counts(df)
        assert len(result) == 1
        assert result.iloc[0]["count"] == 2


# ---------------------------------------------------------------------------
# prepare_rights_holder
# ---------------------------------------------------------------------------

class TestPrepareRightsHolder:
    def test_columns_present(self, sample_df):
        """The rights-holder helper must return 'rightsHolder' and 'count' columns,
        matching the Altair bar chart's encoding."""
        result = prepare_rights_holder(sample_df)
        assert list(result.columns) == ["rightsHolder", "count"]

    def test_top_n_respected(self, sample_df):
        """Passing top_n=2 must return at most 2 rows, so the bar chart never shows
        more entries than the configured limit."""
        result = prepare_rights_holder(sample_df, top_n=2)
        assert len(result) <= 2

    def test_sorted_descending(self, sample_df):
        """Rights holders must be ordered by count descending so the most frequent
        contributor appears first in the horizontal bar chart."""
        result = prepare_rights_holder(sample_df)
        assert result["count"].is_monotonic_decreasing


# ---------------------------------------------------------------------------
# prepare_monthly
# ---------------------------------------------------------------------------

class TestPrepareMonthly:
    def test_columns_present(self, sample_df):
        """The monthly helper must return 'month' and 'count' columns, which the
        Altair bar chart encodes on its x and y axes."""
        result = prepare_monthly(sample_df)
        assert list(result.columns) == ["month", "count"]

    def test_month_values_in_range(self, sample_df):
        """All month values must be integers between 1 and 12, ensuring the x-axis
        label mapping in the Altair chart never receives an out-of-range value."""
        result = prepare_monthly(sample_df)
        assert result["month"].between(1, 12).all()

    def test_invalid_dates_dropped(self):
        """Rows with unparseable eventDate values must be silently dropped, so bad
        data in the CSV does not cause a crash or produce a month=NaN bucket."""
        df = pd.DataFrame({"eventDate": ["not-a-date", "also-bad", "2000-06-15"]})
        result = prepare_monthly(df)
        assert len(result) == 1
        assert result.iloc[0]["month"] == 6