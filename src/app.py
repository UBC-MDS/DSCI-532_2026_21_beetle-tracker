from shiny import App, ui, reactive, render
from shinywidgets import render_widget, output_widget, render_altair
from ipyleaflet import Map, basemaps, GeoJSON, LegendControl
import h3
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import pandas as pd
import os
import altair as alt

# Load the dataset once at startup; all reactive outputs read from this shared dataframe
DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "gbif-beetle.csv"
)
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# Slider bounds derived from the data so they stay correct if the dataset is updated
YEAR_MIN = int(df["year"].min())
YEAR_MAX = int(df["year"].max())

# Dropdown/radio choices derived from the data
REGIONS = ["All"] + sorted(df["countryCode"].dropna().unique().tolist())
BASIS_OF_RECORD = ["All"] + sorted(df["basisOfRecord"].dropna().unique().tolist())

# Available map underlays; keys are displayed in the sidebar dropdown
BASEMAP_OPTIONS = {
    "CartoDB Positron": basemaps.CartoDB.Positron,       # clean light gray, minimal labels
    "CartoDB Dark Matter": basemaps.CartoDB.DarkMatter,  # dark version of Positron
    "Esri Gray Canvas": basemaps.Esri.WorldGrayCanvas,   # very minimal, nearly label-free
    "Esri Topo": basemaps.Esri.WorldTopoMap,             # terrain and topographic detail
    "Satellite": basemaps.Esri.WorldImagery,             # aerial/satellite imagery
}

app_ui = ui.page_fluid(
    ui.tags.style(
        """
        body { background-color: #e8f5e9; }
        .sidebar { background-color: #c8e6c9; }
        .card { background-color: #f1f8e9; }
        .card-header { background-color: #a5d6a7; color: #1b5e20; }
        .value-box { background-color: #c8e6c9 !important; }
    """
    ),
    ui.panel_title("Japanese Beetle Tracker"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_slider(
                id="year_range",
                label="Year Range",
                min=YEAR_MIN,
                max=YEAR_MAX,
                value=[YEAR_MIN, YEAR_MAX],
                sep="",
            ),
            ui.input_selectize(
                id="region",
                label="Filter by Region",
                choices=REGIONS,
                selected="All",
            ),
            ui.input_radio_buttons(
                id="basis_record",
                label="Basis of Record",
                choices=BASIS_OF_RECORD,
                selected="All",
            ),
            # adding in the reset button
            ui.input_action_button(
                id="reset_btn",
                label="Reset Filters",
                class_="btn-warning w-100 mt-2",
            ),
            ui.input_select(
                id="basemap",
                label="Map Underlay",
                choices=list(BASEMAP_OPTIONS.keys()),
                selected="Esri Gray Canvas",
            ),
            ui.input_select(
                id="colormap",
                label="Map Color Scale",
                choices=["viridis", "plasma", "YlOrRd", "Greens", "Blues"],
                selected="plasma",
            ),
            open="desktop",
            width=300,
        ),
        # Summary row
        ui.layout_columns(
            ui.output_ui("vb_total_obs"),
            ui.output_ui("vb_first_recorded"),
            ui.output_ui("vb_status"),
            fill=False,
        ),
        # Map (collapsible)
        ui.accordion(
            ui.accordion_panel(
                "Geographic Distribution Map",
                output_widget("map"),
            ),
            open=True,
        ),
        # Bottom row
        ui.accordion(
            ui.accordion_panel(
                "Observation Charts",
                ui.layout_columns(
                    ui.card(
                        ui.card_header("Occurrences Over Time"),
                        output_widget("plot_timeseries"),
                        full_screen=True,
                    ),
                    ui.card(
                        ui.card_header("Basis of Record"),
                        output_widget("plot_basis"),
                        full_screen=True,
                    ),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("Top Rights Holders"),
                        output_widget("plot_rights_holder"),
                        full_screen=True,
                    ),
                    ui.card(
                        ui.card_header("Seasonal Observations by Month"),
                        output_widget("plot_monthly"),
                        full_screen=True,
                    ),
                    col_widths=[6, 6],
                ),
            ),
            open=True,
        ),
    ),
)


def server(input, output, session):
    # Shared reactive dataframe: filters the full dataset by year range, region, and basis of record.
    # All outputs consume this so each input change triggers one recomputation (not one per output)
    @reactive.calc
    def filtered_df():
        year_min, year_max = input.year_range()
        mask = df["year"].between(year_min, year_max)
        if input.region() != "All":
            mask &= df["countryCode"] == input.region()
        if input.basis_record() != "All":
            mask &= df["basisOfRecord"] == input.basis_record()
        return df[mask]

    # Value box: count of rows in the filtered dataset
    @render.ui
    def vb_total_obs():
        count = len(filtered_df())
        return ui.value_box("Total Observations", f"{count:,}")

    # Value box: earliest year with an observation in the filtered dataset
    @render.ui
    def vb_first_recorded():
        years = filtered_df()["year"].dropna()
        value = str(int(years.min())) if not years.empty else "N/A"
        return ui.value_box("First Recorded", value)

    # Value box: whether any observation exists in the slider's max year
    @render.ui
    def vb_status():
        _, year_max = input.year_range()
        present = (filtered_df()["year"] == year_max).any()
        value = "Present" if present else "Not Detected"
        return ui.value_box(f"Status in Region as of {year_max}", value)

    # Line chart: number of observations per year across the filtered dataset
    @render_altair
    def plot_timeseries():
        counts = filtered_df().groupby("year").size().reset_index(name="count")

        nearest = alt.selection_point(
            nearest=True, on="mouseover", fields=["year"], empty=False
        )

        line = (
            alt.Chart(counts)
            .mark_line()
            .encode(
                x=alt.X("year:Q", title="Year", axis=alt.Axis(tickCount=6, format="d")),
                y=alt.Y("count:Q", title="Observations"),
            )
        )

        points = (
            line.mark_point()
            .encode(
                opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
                tooltip=["year:Q", "count:Q"],
            )
            .add_params(nearest)
        )

        chart = (line + points).properties(width="container", height=300)
        return chart

    # Pie chart: share of each basisOfRecord category in the filtered dataset
    @render_altair
    def plot_basis():
        counts = filtered_df()["basisOfRecord"].value_counts().reset_index()
        counts.columns = ["basisOfRecord", "count"]

        chart = (
            alt.Chart(counts)
            .mark_arc()
            .encode(
                theta=alt.Theta("count:Q"),
                color=alt.Color(
                    "basisOfRecord:N", legend=alt.Legend(title="Basis of Record")
                ),
                tooltip=["basisOfRecord", "count"],
            )
            .properties(width="container", height=350)
        )
        return chart

    # Bar chart: top 10 rights holders
    @render_altair
    def plot_rights_holder():
        counts = (
            filtered_df()["rightsHolder"].dropna().value_counts().head(10).reset_index()
        )
        counts.columns = ["rightsHolder", "count"]

        chart = (
            alt.Chart(counts)
            .mark_bar()
            .encode(
                x=alt.X("count:Q", title="Observations"),
                y=alt.Y("rightsHolder:N", sort="-x", title="Rights Holder"),
                tooltip=["rightsHolder", "count"],
            )
            .properties(width="container", height=300)
        )
        return chart

    # Bar chart: observations by month
    @render_altair
    def plot_monthly():
        monthly = (
            filtered_df()
            .assign(
                month=pd.to_datetime(
                    filtered_df()["eventDate"], errors="coerce"
                ).dt.month
            )
            .dropna(subset=["month"])
            .groupby("month")
            .size()
            .reset_index(name="count")
        )
        monthly["month"] = monthly["month"].astype(int)

        month_names = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }
        monthly["month_name"] = monthly["month"].map(month_names)

        chart = (
            alt.Chart(monthly)
            .mark_bar()
            .encode(
                x=alt.X(
                    "month:O",
                    title="Month",
                    axis=alt.Axis(
                        labelExpr="{'1':'Jan','2':'Feb','3':'Mar','4':'Apr','5':'May','6':'Jun','7':'Jul','8':'Aug','9':'Sep','10':'Oct','11':'Nov','12':'Dec'}[datum.label]"
                    ),
                ),
                y=alt.Y("count:Q", title="Observations"),
                tooltip=["month_name", "count"],
            )
            .properties(width="container", height=300)
        )
        return chart
        
    
    # This map was coded with Claude's assistance. Claude suggested:
    #  - Use H3 hexagonal binning over ipyleaflet's built-in Heatmap layer
    #  - H3 provies the hexagon shapes
    #  - We hand the shapes over to pyleaflet (no longer using heatmap)
    #  - Use ipyleaflet's LegendControl to add an on-map legend
    #  - GeoJSON used to represent hexagon shapes, which pyleaflet understands
    # Map with H3 hex bins showing observation density.
    # Reactively redraws whenever any sidebar filter or display option changes
    @render_widget
    def map():
        # Base map tile layer is selected by the user via the sidebar dropdown
        m = Map(center=(20, 0),
                zoom=2,
                basemap=BASEMAP_OPTIONS[input.basemap()],
                layout={"height": "450px"})

        # Drop rows with missing coordinates and clamp to valid lat/lon ranges
        pts = filtered_df()[["decimalLatitude", "decimalLongitude"]].dropna()
        pts = pts[pts["decimalLatitude"].between(-90, 90) & pts["decimalLongitude"].between(-180, 180)]

        # Return a plain empty map if the current filter selection has no data
        if pts.empty:
            return m

        # --- H3 hexagonal binning ---
        # Resolution adapts to the number of points so the GeoJSON payload stays manageable:
        # large datasets use resolution 2 (~5,882 global cells) to avoid browser timeouts,
        # while smaller datasets use resolution 3 (~41,163 cells) for finer detail.
        resolution = 2 if len(pts) > 5_000 else 3
        latlng_to_cell = np.vectorize(lambda lat, lng: h3.latlng_to_cell(lat, lng, resolution))
        cells = latlng_to_cell(pts["decimalLatitude"].values, pts["decimalLongitude"].values)
        
        # Count observations per cell; most-frequent cells will receive the darkest color
        counts = pd.Series(cells).value_counts()

        # Colormap is selected by the user; count is normalised to [0, 1] against the max
        cmap = cm.get_cmap(input.colormap())
        max_count = counts.max()

        # Build a GeoJSON feature for each occupied cell
        features = []
        for cell, count in counts.items():
            # h3.cell_to_boundary returns vertices as (lat, lng); GeoJSON expects [lng, lat]
            boundary = h3.cell_to_boundary(cell)
            coords = [[lng, lat] for lat, lng in boundary]
            coords.append(coords[0])  # close the polygon ring
            color = mcolors.to_hex(cmap(count / max_count))
            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coords]},
                "properties": {"style": {
                    "color": color,       # border color
                    "fillColor": color,   # fill color
                    "fillOpacity": 0.7,
                    "weight": 0.3,        # border thickness
                }},
            })

        # Add the hex bin layer; style_callback applies the per-feature color stored above
        m.add_layer(GeoJSON(
            data={"type": "FeatureCollection", "features": features},
            style_callback=lambda f: f["properties"]["style"],
        ))

        # --- Legend ---
        # 5 evenly-spaced steps spanning the actual count range in the current filtered data
        legend_steps = ["Very Low", "Low", "Medium", "High", "Very High"]
        legend_colors = {
            f"{label} ({max(1, round(max_count * i / 4)):,})": mcolors.to_hex(cmap(i / 4))
            for i, label in enumerate(legend_steps)
        }
        m.add_control(LegendControl(legend_colors, title="Observations", position="bottomright"))

        return m

    # reset button
    @reactive.effect
    @reactive.event(input.reset_btn)
    def reset_filters():
        ui.update_slider("year_range", value=[YEAR_MIN, YEAR_MAX])
        ui.update_selectize("region", selected="All")
        ui.update_radio_buttons("basis_record", selected="All")


app = App(app_ui, server, static_assets=os.path.join(os.path.dirname(__file__), "www"))
