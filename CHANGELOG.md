# Change Log

## 0.3.0

### Added

#### AI Chat Panel

An AI-powered chat panel has been added to the dashboard. Users can ask questions about the beetle data and receive responses from a language model. A `greeting.md` file provides the initial AI greeting message. (#66)

#### Map Hover Info

Hovering over map regions now displays a tooltip showing the top 5 beetle count locations for that area. (#75)

#### GitHub API Key Support

The dashboard now supports authentication via a GitHub API key for accessing the AI features, configured through a `.env` file. (#63)

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
* Added a CSV download button to the AI Explorer page that downloads the QueryChat-filtered dataframe (`#64`).

#### Reset Button

This button on the dash board will reset all inputs to original.

### Changed

### Fixed

### Known Issues

### Reflection
