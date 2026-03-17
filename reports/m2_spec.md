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
| 7   | When I am reviewing the historical progression of beetle activity, I want to observe how observation density shifts geographically on the map as I adjust the year range, so I can understand whether the infestation is expanding into new areas or intensifying in established ones. | Implemented |                               |
| 8   | When I am assessing the overall scale of beetle activity within a selected region and time period, I want the Total Observations indicator to update automatically with my filters, so I can quickly gauge the magnitude of activity without analyzing multiple charts. | Implemented |                               |
| 9   | When I click a selected area on the map, I want the rest of the dashboard to update to that area so I can explore observations more directly without relying only on sidebar filters. | Implemented | Map click filters dashboard outputs |

---

## 2.2 Component Inventory

### Inputs

| ID             | Type  | Shiny widget                | Description                              | Job story |
| -------------- | ----- | --------------------------- | ---------------------------------------- | --------- |
| `year_range`   | Input | `ui.input_slider()`         | Dual-handle slider selecting a year range; bounds are derived from the dataset at startup | #1, #5 |
| `region`       | Input | `ui.input_selectize()`      | Dropdown to filter by region; users see country names while filtering still uses the underlying `countryCode` values | #2, #6 |
| `basis_record` | Input | `ui.input_radio_buttons()`  | Radio buttons to filter by `basisOfRecord`; choices include "All" plus each unique value in the data | #2 |
| `clear_map_selection` | Input | `ui.input_action_button()` | Button that clears the currently selected map hex without resetting the other filters | #9 |
| `basemap`      | Input | `ui.input_select()`         | Dropdown to choose the map tile underlay (CartoDB Positron, CartoDB Dark Matter, Esri Gray Canvas, Esri Topo, Satellite) | #2 |
| `colormap`     | Input | `ui.input_select()`         | Dropdown to choose the colour scale for hex-bin density (viridis, plasma, YlOrRd, Greens, Blues) | #2 |

### Reactive intermediary

| ID            | Type             | Shiny mechanism    | Depends on                              | Description |
| ------------- | ---------------- | ------------------ | --------------------------------------- | ----------- |
| `selected_map_cell` | Reactive value | `reactive.value()` | map click, reset button, clear-map button, main filters | Stores the currently selected H3 hex cell so the map can behave like an input |
| `map_points_df` | Reactive calc | `@reactive.calc` | `filtered_expr` | Builds the filtered coordinate dataset used to draw the map and assign H3 cells |
| `filtered_df` | Reactive calc    | `@reactive.calc`   | `filtered_expr`, `selected_map_cell`  | Applies the selected map hex as an additional filter on top of the main year/region/basis filters so all outputs can react to a clicked map area |

### Outputs

| ID                   | Type   | Shiny renderer   | Depends on                         | Job story |
| -------------------- | ------ | ---------------- | ---------------------------------- | --------- |
| `vb_total_obs`       | Output | `@render.ui`     | `filtered_df`                      | #1        |
| `vb_first_recorded`  | Output | `@render.ui`     | `filtered_df`                      | #5        |
| `vb_status`          | Output | `@render.ui`     | `filtered_df`, `year_range`, `region`, `selected_map_cell` | #5, #6, #9 |
| `map`                | Output | `@render_widget` | `filtered_df`, `basemap`, `colormap` | #2, #6  |
| `map_selection_status` | Output | `@render.ui`   | `selected_map_cell`, `filtered_df` | #9 |
| `plot_timeseries`    | Output | `@render_altair` | `filtered_df`                      | #1, #5    |
| `plot_basis`         | Output | `@render_altair` | `filtered_df`                      | #2        |
| `plot_rights_holder` | Output | `@render_altair` | `filtered_df`                      | #3        |
| `plot_monthly`       | Output | `@render_altair` | `filtered_df`                      | #4        |

---

## 2.3 Reactivity Diagram

The main sidebar filters (`year_range`, `region`, `basis_record`) feed into a base filtered query. The map is rendered from this filtered spatial dataset, and clicking a hexagon stores the selected H3 cell as a reactive value. That selected cell then feeds into `filtered_df`, which acts as the shared filtered dataset for the dashboard outputs. The `clear_map_selection` button and reset button both clear the selected map cell. The display inputs (`basemap`, `colormap`) still flow directly into the map widget only. `vb_status` also reads `year_range` directly to obtain the upper-bound year for its label.

``` mermaid
flowchart TD
  A[/year_range/] --> Q{{filtered_expr}}
  B[/region/] --> Q
  C[/basis_record/] --> Q
  Q --> M{{map_points_df}}
  M --> P3([map])
  P3 --> S{{selected_map_cell}}
  S --> F{{filtered_df}}
  A --> VB3
  B --> VB3
  D[/basemap/] --> P3
  E[/colormap/] --> P3
  R[/clear_map_selection/] --> S
  F --> VB1([vb_total_obs])
  F --> VB2([vb_first_recorded])
  F --> VB3([vb_status])
  F --> MS([map_selection_status])
  F --> P1([plot_timeseries])
  F --> P2([plot_basis])
  F --> P4([plot_rights_holder])
  F --> P5([plot_monthly])
```

---

## 2.4 Calculation Details

### `filtered_df`

**Inputs it depends on:** `filtered_expr`, `selected_map_cell`

**Transformation:** First applies the main sidebar filters (year range, region, and basis of record) through the base filtered query. If no map hex is selected, the resulting filtered dataset is returned as-is. If a map hex is selected, the dataset is further restricted to records whose coordinates fall within the selected H3 cell. This allows the map to act as an input component and drive the rest of the dashboard outputs.

**Outputs that consume it:** `vb_total_obs`, `vb_first_recorded`, `vb_status`, `map_selection_status`, `plot_timeseries`, `plot_basis`, `plot_rights_holder`, `plot_monthly`

## Complexity Enhancement

The dashboard includes two interaction enhancements beyond the original filtering controls:

1. A reset button that restores the sidebar filters to their default state.
2. A map-click interaction that allows users to select an H3 hexagon and use it as an input-like filter for the rest of the dashboard.

These enhancements improve usability by supporting faster exploration and more direct interaction with the spatial view.
