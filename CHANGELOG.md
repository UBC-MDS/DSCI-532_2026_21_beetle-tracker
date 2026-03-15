# Change Log

## 0.4.0

### Added

- Added `utils.py` with pure helper functions extracted from `app.py` for testability (`apply_filters`, `compute_first_recorded`, `compute_status`, `prepare_timeseries`, `prepare_basis_counts`, `prepare_rights_holder`, `prepare_monthly`) (#96)
- Added 25 unit tests in `tests/test_utils.py` covering all filtering and chart data preparation logic (#96)
- Added 5 Playwright end-to-end tests in `tests/test_app_playwright.py` covering year range filter, reset button, first recorded value box, basis of record filter, and download CSV button (#96)
- Added `conftest.py` to configure the test path for `utils.py` (#96)
- Added test instructions to README (#98)
- Added "How to Use the Dashboard" section to README explaining all sidebar controls, value boxes, map, and AI Explorer tab (#100)

### Changed

- Added `pytest`, `pytest-playwright`, and `playwright` to `environment.yml` (#97)
- Refactored `filtered_df()`, `vb_first_recorded()`, and `vb_status()` in `app.py` to use `utils.py` helper functions (#96)

### Fixed

- Addressed feedback: added dashboard usage instructions to README to reduce learning curve for new users (#100)

- **Feedback prioritization issue link:** #86

---

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

#### Basis of Record Pie Chart(AI filtered) 
Added a Basis of Record pie chart to the AI Explorer panel to visualize the distribution of record types in the AI-filtered dataset.

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

