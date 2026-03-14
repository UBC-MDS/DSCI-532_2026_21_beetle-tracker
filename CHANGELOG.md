# Change Log

## 0.3.0

### Added

#### AI Chat Panel

An AI-powered chat panel has been added to the dashboard. Users can ask questions about the beetle data and receive responses from a language model. A `greeting.md` file provides the initial AI greeting message. (#66)

#### Map Hover Info

Hovering over map regions now displays a tooltip showing the top 5 beetle count locations for that area. (#75)

#### GitHub API Key Support

The dashboard now supports authentication via a GitHub API key for accessing the AI features, configured through a `.env` file. (#63)

#### CSV download button

Added a CSV download button to the AI Explorer page that downloads the QueryChat-filtered dataframe (`#64`).

### Changed

#### Dashboard Runs Without API Keys

The dashboard gracefully handles missing API keys. All non-AI features remain fully functional when no key is configured, and an informational message is shown instead of an error. (#75)

#### Updated README and Setup Instructions

README has been expanded with clearer installation and configuration instructions. `environment.yml` and `requirements.txt` updated with new dependencies (`anthropic`, `python-dotenv`, etc.). (#65)

### Fixed

#### Map Graying Out

Optimised map loading to prevent the map from graying out under certain rendering conditions. (#69)

---

## 0.2.0

### Added

* Added a plot of occurrences over time on the AI-powered chat panel. Now, you can modify the filtered dataframe by telling the AI which filters to apply, the results of which then show up on the chart.

#### Reset Button

This button on the dash board will reset all inputs to original.

### Changed

### Fixed

### Known Issues

### Reflection

## [0.4.0] - 2026-03-17

### Added

* Added `prep_data.py` one-time ETL script to convert raw CSV to Parquet format (`data/processed/`)

### Changed

* Switched data loading from eager `pd.read_csv` to lazy ibis + DuckDB connection to Parquet file
* Replaced `filtered_df()` with `filtered_expr()` — all filtering now happens at the DuckDB query layer before any data enters memory
* Updated all dashboard outputs (value boxes, charts, map) to call `.execute()` individually at render time
* Month extraction in `plot_monthly` now uses regex to handle mixed `eventDate` formats in the raw data

### Fixed

* Fixed `countryCode` and `basisOfRecord` dropdown population to use ibis-native null filtering instead of pandas `.dropna()`
* Fixed `vb_status` crash caused by `_` tuple unpacking overwriting the ibis `_` column reference import

* **Feedback prioritization issue link:** #...

### Known Issues

* <!-- Anything incomplete or broken TAs should be aware of (so it isn't mistaken for unfinished work). -->

### Release Highlight: [Name of your advanced feature]

<!-- One short paragraph describing what you built and what it does for the user. -->

* **Option chosen:** A / B / C / D
* **PR:** #...
* **Why this option over the others:** <!-- 1–2 sentences; link to your feature prioritization issue -->
* **Feature prioritization issue link:** #...

### Collaboration

<!-- Summary of workflow or collaboration improvements made since M3. -->

* **CONTRIBUTING.md:** <!-- Link to the PR that updated it with your M3 retrospective and M4 norms. -->
* **M3 retrospective:** <!-- What changed in your workflow after M3 collaboration feedback. -->
* **M4:** <!-- What you tried or improved this milestone. -->

### Reflection

<!-- Standard (see General Guidelines): what the dashboard does well, current limitations,
     any intentional deviations from DSCI 531 visualization best practices. -->

<!-- Trade-offs: one sentence on feedback prioritization - full rationale is in #<issue> and ### Changed above. -->

<!-- Most useful: which lecture, material, or feedback shaped your work most this milestone,
     and anything you wish had been covered. -->
