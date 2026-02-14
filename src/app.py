from shiny import App, ui
from shinywidgets import render_widget, output_widget
from ipyleaflet import Map

app_ui = ui.page_fluid(
    ui.tags.style("""
        body { background-color: #e8f5e9; }
        .sidebar { background-color: #c8e6c9; }
        .card { background-color: #f1f8e9; }
        .card-header { background-color: #a5d6a7; color: #1b5e20; }
        .value-box { background-color: #c8e6c9 !important; }
    """),
    ui.panel_title("Japanese Beetle — Invasive Species Tracker"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_slider(
                id="year_range",
                label="Year Range",
                min=1900,
                max=2026,
                value=[1900, 2026],
                sep="",
            ),
            ui.input_selectize(
                id="region",
                label="Filter by Region",
                choices=["All", "Australia", "Canada", "Japan", "Placeholder"],
                selected="All",
            ),
            ui.input_radio_buttons(
                id="basis_record",
                label="Basis of Record",
                choices={
                    "ALL": "All Observations",
                    "SPECIMEN": "Preserved specimen",
                    "OCCURRENCE": "Occurrence",
                },
                selected="ALL",
            ),
            open="desktop",
        ),
        # Summary row
        ui.layout_columns(
            ui.value_box("Total Observations", "532"),
            ui.value_box("First Recorded", "2012"),
            ui.value_box("Status in Region", "Present"),
            fill=False,
        ),
        # Map
        ui.card(
            ui.card_header("Geographic Distribution Map"),
            output_widget("map"),
            full_screen=True,
        ),
        # Bottom row
        ui.layout_columns(
            ui.card(
                ui.card_header("Occurrences Over Time"),
                "Placeholder: Time series chart will go here",
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Basis of Record"),
                "Placeholder: Pie chart of record types will go here",
                full_screen=True,
            ),
            col_widths=[6, 6],
        ),
    ),
)


def server(input, output, session):
    @render_widget
    def map():
        return Map(center=(20, 0), zoom=2, layout={"height": "450px"})


app = App(app_ui, server)
