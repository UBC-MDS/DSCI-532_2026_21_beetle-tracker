"""
utils.py – Pure helper functions extracted from app.py.

These functions contain no Shiny reactive state, so they can be imported and
tested in isolation with pytest without launching the full application.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def apply_filters(
    df: pd.DataFrame,
    year_min: int,
    year_max: int,
    region: str = "All",
    basis_of_record: str = "All",
) -> pd.DataFrame:
    """Return rows of *df* that satisfy all three sidebar filter conditions.

    Parameters
    ----------
    df : pd.DataFrame
        Full beetle observation dataset.
    year_min, year_max : int
        Inclusive year bounds from the slider.
    region : str
        Country code to keep, or ``"All"`` to skip region filtering.
    basis_of_record : str
        Basis-of-record category to keep, or ``"All"`` to skip that filter.

    Returns
    -------
    pd.DataFrame
        Filtered subset (a copy, so the caller can modify it safely).
    """
    mask = df["year"].between(year_min, year_max)
    if region != "All":
        mask &= df["countryCode"] == region
    if basis_of_record != "All":
        mask &= df["basisOfRecord"] == basis_of_record
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Value-box helpers
# ---------------------------------------------------------------------------

def compute_first_recorded(df: pd.DataFrame) -> str:
    """Return the earliest year with an observation as a string, or ``"N/A"``.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered dataset that must contain a ``"year"`` column.

    Returns
    -------
    str
        Four-digit year string (e.g. ``"1998"``), or ``"N/A"`` when *df* is
        empty or contains only NaN years.
    """
    years = df["year"].dropna()
    if years.empty:
        return "N/A"
    return str(int(years.min()))


def compute_status(df: pd.DataFrame, year_max: int) -> str:
    """Return ``"Present"`` if any row matches *year_max*, else ``"Not Detected"``.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered dataset.
    year_max : int
        The upper bound of the year slider (the reference year for presence).

    Returns
    -------
    str
        ``"Present"`` or ``"Not Detected"``.
    """
    present = (df["year"] == year_max).any()
    return "Present" if present else "Not Detected"


# ---------------------------------------------------------------------------
# Chart data helpers
# ---------------------------------------------------------------------------

def prepare_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate observation counts by year for the time-series line chart.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered dataset with a ``"year"`` column.

    Returns
    -------
    pd.DataFrame
        Two-column DataFrame: ``year`` (int/float) and ``count`` (int).
    """
    return df.groupby("year").size().reset_index(name="count")


def prepare_basis_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Count observations per ``basisOfRecord`` category for the pie chart.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered dataset with a ``"basisOfRecord"`` column.

    Returns
    -------
    pd.DataFrame
        Two-column DataFrame: ``basisOfRecord`` (str) and ``count`` (int),
        sorted descending by count.
    """
    counts = df["basisOfRecord"].dropna().value_counts().reset_index()
    counts.columns = ["basisOfRecord", "count"]
    return counts


def prepare_rights_holder(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return the top-*n* rights holders by observation count.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered dataset with a ``"rightsHolder"`` column.
    top_n : int
        Number of top holders to return (default 10).

    Returns
    -------
    pd.DataFrame
        Two-column DataFrame: ``rightsHolder`` (str) and ``count`` (int).
    """
    counts = df["rightsHolder"].dropna().value_counts().head(top_n).reset_index()
    counts.columns = ["rightsHolder", "count"]
    return counts


def prepare_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate observation counts by calendar month for the bar chart.

    Rows with unparseable ``eventDate`` values are silently dropped.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered dataset with an ``"eventDate"`` column.

    Returns
    -------
    pd.DataFrame
        Two-column DataFrame: ``month`` (int 1–12) and ``count`` (int).
        Months with zero observations are absent (sparse).
    """
    monthly = (
        df.assign(
            month=pd.to_datetime(
                df["eventDate"], errors="coerce", utc=True, format="mixed"
            ).dt.month
        )
        .dropna(subset=["month"])
        .groupby("month")
        .size()
        .reset_index(name="count")
    )
    monthly["month"] = monthly["month"].astype(int)
    return monthly