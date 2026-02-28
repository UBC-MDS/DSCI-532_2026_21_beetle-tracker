# App Specification

## 2.1 Updated Job Stories

| #   | Job Story                       | Status         | Notes                         |
| --- | ------------------------------- | -------------- | ----------------------------- |
| 1   | When I want to know how many observations are in a time frame, I want to be able to select a start and end year, so I can see the total observations in a value box. | Implemented |                               |
| 2   | When I want to visualize all the observations on the map, I will first filter the data by changing the filter selection on the left sidebar (time range, region, etc.), so the map will update with a marker or heatmap for all the observations. | Implemented | Use H3 library for hex cell calculations |
| 3   | When I want to know which organizations or individuals contribute the most beetle records, I want to see a ranked bar chart of top rights holders, so I can identify the key contributors to the dataset. | Implemented |  |
| 4   | When I want to plan pest control or fieldwork, I want to see which months have the highest beetle activity, so I can time my interventions or observations effectively. | Implemented | |
| 5   | When I am assessing risk and developing prevention methods, I want to see the spread of the beetle from first observation to a widespread established population so I can plean when prevention strategies should be implemented.| implemented |                               |
| 6   | When I am curious about what regions are at risk, I want to visualize on the map along what latitudes infestations are present so I can assess if my region is at risk. | implemented |                               |
| 7   | When I … I want to … so I can … |  |                               |
| 8   | When I … I want to … so I can … |  |                               |

---

## 2.2 Component Inventory

### Inputs

| ID             | Type  | Shiny widget                | Description                              | Job story |
| -------------- | ----- | --------------------------- | ---------------------------------------- | --------- |
| `year_range`   | Input | `ui.input_slider()`         | Dual-handle slider selecting a year range; bounds are derived from the dataset at startup | #1, #5 |
| `region`       | Input | `ui.input_selectize()`      | Dropdown to filter by country code; choices include "All" plus each unique `countryCode` in the data | #2, #6 |
| `basis_record` | Input | `ui.input_radio_buttons()`  | Radio buttons to filter by `basisOfRecord`; choices include "All" plus each unique value in the data | #2 |
| `basemap`      | Input | `ui.input_select()`         | Dropdown to choose the map tile underlay (CartoDB Positron, CartoDB Dark Matter, Esri Gray Canvas, Esri Topo, Satellite) | #2 |
| `colormap`     | Input | `ui.input_select()`         | Dropdown to choose the colour scale for hex-bin density (viridis, plasma, YlOrRd, Greens, Blues) | #2 |

### Reactive intermediary

| ID            | Type             | Shiny mechanism    | Depends on                              | Description |
| ------------- | ---------------- | ------------------ | --------------------------------------- | ----------- |
| `filtered_df` | Reactive calc    | `@reactive.calc`   | `year_range`, `region`, `basis_record`  | Filters the full dataset once per input change; all outputs consume this shared result so each filter change triggers only one data recomputation |

### Outputs

| ID                   | Type   | Shiny renderer   | Depends on                         | Job story |
| -------------------- | ------ | ---------------- | ---------------------------------- | --------- |
| `vb_total_obs`       | Output | `@render.ui`     | `filtered_df`                      | #1        |
| `vb_first_recorded`  | Output | `@render.ui`     | `filtered_df`                      | #5        |
| `vb_status`          | Output | `@render.ui`     | `filtered_df`, `year_range`        | #5, #6    |
| `map`                | Output | `@render_widget` | `filtered_df`, `basemap`, `colormap` | #2, #6  |
| `plot_timeseries`    | Output | `@render_altair` | `filtered_df`                      | #1, #5    |
| `plot_basis`         | Output | `@render_altair` | `filtered_df`                      | #2        |
| `plot_rights_holder` | Output | `@render_altair` | `filtered_df`                      | #3        |
| `plot_monthly`       | Output | `@render_altair` | `filtered_df`                      | #4        |

---

## 2.3 Reactivity Diagram

All three filter inputs (`year_range`, `region`, `basis_record`) feed into a single shared `@reactive.calc` (`filtered_df`). Every output reads from `filtered_df`, so a change to any filter triggers one recomputation of the filtered data and then re-renders all outputs. The two display inputs (`basemap`, `colormap`) bypass `filtered_df` and flow directly into the map widget only. `vb_status` also reads `year_range` directly to obtain the upper-bound year for its label.

``` mermaid
flowchart TD
  A[/year_range/] --> F{{filtered_df}}
  B[/region/] --> F
  C[/basis_record/] --> F
  D[/basemap/] --> P3
  E[/colormap/] --> P3
  A --> VB3
  F --> VB1([vb_total_obs])
  F --> VB2([vb_first_recorded])
  F --> VB3([vb_status])
  F --> P1([plot_timeseries])
  F --> P2([plot_basis])
  F --> P3([map])
  F --> P4([plot_rights_holder])
  F --> P5([plot_monthly])
```

---

## 2.4 Calculation Details

### `filtered_df`

**Inputs it depends on:** `year_range`, `region`, `basis_record`

**Transformation:** Filters the full dataset (`df`) to rows whose `year` falls within the selected range (inclusive). If `region` is not `"All"`, further restricts to rows where `countryCode` matches the selection. If `basis_record` is not `"All"`, further restricts to rows where `basisOfRecord` matches the selection. Returns the resulting subset as a DataFrame.

**Outputs that consume it:** `vb_total_obs`, `vb_first_recorded`, `vb_status`, `map`, `plot_timeseries`, `plot_basis`, `plot_rights_holder`, `plot_monthly` (every output in the app).

## Complexity Enhancement

Reset button which resets all filters back to original (none). This button will improve user experience by simplifying the resetting process, allowing them to make more queries faster.
