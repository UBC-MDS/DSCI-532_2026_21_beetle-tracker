# App Specification

## 2.1 Updated Job Stories

| #   | Job Story                       | Status         | Notes                         |
| --- | ------------------------------- | -------------- | ----------------------------- |
| 1   | When I want to know how many observations are in a time frame, I want to be able to select a start and end year, so I can see the total observations in a value box. | Implemented |                               |
| 2   | When I … I want to … so I can … |  |                               |
| 3   | When I want to know which organizations or individuals contribute the most beetle records, I want to see a ranked bar chart of top rights holders, so I can identify the key contributors to the dataset. | Implemented |  |
| 4   | When I want to plan pest control or fieldwork, I want to see which months have the highest beetle activity, so I can time my interventions or observations effectively. | Implemented | |
| 5   | When I am assessing risk and developing prevention methods, I want to see the spread of the beetle from first observation to a widespread established population so I can plean when prevention strategies should be implemented.| implemented |                               |
| 6   | When I am curious about what regions are at risk, I want to visualize on the map along what latitudes infestations are present so I can assess if my region is at risk. | implemented |                               |
| 7   | When I am reviewing the historical progression of beetle activity, I want to observe how observation density shifts geographically on the map as I adjust the year range, so I can understand whether the infestation is expanding into new areas or intensifying in established ones. | Implemented |                               |
| 8   | When I am assessing the overall scale of beetle activity within a selected region and time period, I want the Total Observations indicator to update automatically with my filters, so I can quickly gauge the magnitude of activity without analyzing multiple charts. | Implemented |                               |

---

## 2.2 Component Inventory

| ID            | Type          | Shiny widget / renderer | Depends on                   | Job story  |
| ------------- | ------------- | ----------------------- | ---------------------------- | ---------- |
| `input_year`  | Input         | `ui.input_slider()`     | —                            | #1         |
| `plot_rights_holder`   | Output | `render_altair` | `input_year`, `input_region`, `input_basis_record` | #3 |
| `plot_monthly`         | Output | `render_altair` | `input_year`, `input_region`, `input_basis_record` | #4 |

---

## 2.3 Reactivity Diagram

---

## 2.4 Calculation Details

## Complexity Enhancement

Reset button which resets all filters back to original (none). This button will improve user experience by simplifying the resetting process, allowing them to make more queries faster.
