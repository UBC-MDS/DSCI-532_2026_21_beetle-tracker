from shiny import App, ui, reactive, render
from shinywidgets import render_widget, output_widget, render_altair
from ipyleaflet import Map
import pandas as pd
import matplotlib.pyplot as plt
import os
import altair as alt

# Load the dataset once at startup; all reactive outputs read from this shared dataframe
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "gbif-beetle.csv")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# Slider bounds derived from the data so they stay correct if the dataset is updated
YEAR_MIN = int(df["year"].min())
YEAR_MAX = int(df["year"].max())

# Dropdown/radio choices derived from the data
REGIONS = ["All"] + sorted(df["countryCode"].dropna().unique().tolist())
BASIS_OF_RECORD = ["All"] + sorted(df["basisOfRecord"].dropna().unique().tolist())

app_ui = ui.page_fluid(
    ui.tags.style("""
        body { background-color: #e8f5e9; }
        .sidebar { background-color: #c8e6c9; }
        .card { background-color: #f1f8e9; }
        .card-header { background-color: #a5d6a7; color: #1b5e20; }
        .value-box { background-color: #c8e6c9 !important; }
    """),
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
            open="desktop",
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
        counts = (
            filtered_df()
            .groupby("year")
            .size()
            .reset_index(name="count")
        )
        chart = alt.Chart(counts).mark_line().encode(
            x=alt.X("year:Q", title="Year", axis=alt.Axis(tickCount=6, format="d")),
            y=alt.Y("count:Q", title="Observations"),
            tooltip=["year", "count"]
        ).properties(
            width="container",
            height=300
        )
        return chart

    # Pie chart: share of each basisOfRecord category in the filtered dataset
    @render_altair
    def plot_basis():
        counts = (
            filtered_df()["basisOfRecord"]
            .value_counts()
            .reset_index()
        )
        counts.columns = ["basisOfRecord", "count"]
        
        chart = alt.Chart(counts).mark_arc().encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color("basisOfRecord:N", legend=alt.Legend(title="Basis of Record")),
            tooltip=["basisOfRecord", "count"]
        ).properties(
            width="container",
            height=350
        )
        return chart
    
    # Interactive line chart with points and tooltips
    @render_altair
    def plot_timeseries():
        counts = (
            filtered_df()
            .groupby("year")
            .size()
            .reset_index(name="count")
        )
        
        nearest = alt.selection_point(nearest=True, on="mouseover", fields=["year"], empty=False)
        
        line = alt.Chart(counts).mark_line().encode(
            x=alt.X("year:Q", title="Year", axis=alt.Axis(tickCount=6, format="d")),
            y=alt.Y("count:Q", title="Observations"),
        )
        
        points = line.mark_point().encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
            tooltip=["year:Q", "count:Q"]
        ).add_params(nearest)
        
        chart = (line + points).properties(width="container", height=300)
        return chart

    # Static map centered on the world; will be made reactive in a future milestone
    @render_widget
    def map():
        return Map(center=(20, 0), zoom=2, layout={"height": "450px"})

app = App(
    app_ui,
    server,
    static_assets=os.path.join(os.path.dirname(__file__), "www")
)
