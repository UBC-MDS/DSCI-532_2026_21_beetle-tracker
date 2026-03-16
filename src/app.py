from shiny import App, ui, reactive, render
from shinywidgets import render_widget, output_widget
from querychat import QueryChat
from chatlas import ChatAnthropic, ChatGithub
from ipyleaflet import Map, Polygon, WidgetControl
import ipywidgets as widgets
import h3
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import pandas as pd
import os
import altair as alt
from dotenv import load_dotenv
import io
import ibis
import pycountry
from ibis import _

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# LAZY data loading. this just connects to duckdb, and tells it where the parquet file is
PARQUET_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "gbif-beetle.parquet"
)
con = ibis.duckdb.connect()
beetle_df = con.read_parquet(PARQUET_PATH)

# just to get min/max year for sliders. not a lot of data though.
_meta = beetle_df.aggregate(
    year_min=beetle_df["year"].min(),
    year_max=beetle_df["year"].max(),
).execute()

YEAR_MIN = int(_meta["year_min"].iloc[0])
YEAR_MAX = int(_meta["year_max"].iloc[0])

# Unique sorted values for selectize / radio buttons
REGION_CODES = (
    beetle_df.filter(_.countryCode.notnull())
    .select("countryCode")
    .distinct()
    .order_by("countryCode")
    .execute()["countryCode"]
    .tolist()
)
REGIONS = {
    "All": "All",
    **{
        code: (
            country.name
            if (country := pycountry.countries.get(alpha_2=code)) is not None
            else code
        )
        for code in REGION_CODES
    },
}
BASIS_OF_RECORD = ["All"] + (
    beetle_df.filter(_.basisOfRecord.notnull())
    .select("basisOfRecord")
    .distinct()
    .order_by("basisOfRecord")
    .execute()["basisOfRecord"]
    .tolist()
)

# querychat operates on an in-memory DataFrame.  We load it once here so it
# doesn't have to re-read the file on every chat turn.  This is the *only*
# place we pull the whole dataset into RAM
df_full = beetle_df.execute()

# Pre-compute H3 cell boundaries at startup (resolution 2) so the server
# can create Polygon widgets once and only mutate their properties reactively.
_pts_startup = (
    beetle_df
    .select(["decimalLatitude", "decimalLongitude"])
    .filter(
        _.decimalLatitude.notnull()
        & _.decimalLongitude.notnull()
        & _.decimalLatitude.between(-90, 90)
        & _.decimalLongitude.between(-180, 180)
    )
    .execute()
)
_fn = np.vectorize(lambda lat, lng: h3.latlng_to_cell(lat, lng, 2))
_pts_startup["cell"] = _fn(
    _pts_startup["decimalLatitude"].values,
    _pts_startup["decimalLongitude"].values,
)
CELL_LOCATIONS: dict = {}
for _cell in _pts_startup["cell"].unique():
    _boundary = h3.cell_to_boundary(_cell)
    CELL_LOCATIONS[_cell] = [(lat, lng) for lat, lng in _boundary]



# Reuse the same H3 cell assignment logic for both drawing and filtering map data.
def add_h3_cells(data: pd.DataFrame, resolution: int) -> pd.DataFrame:
    data = data.copy()
    latlng_to_cell = np.vectorize(
        lambda lat, lng: h3.latlng_to_cell(lat, lng, resolution)
    )
    data["cell"] = latlng_to_cell(
        data["decimalLatitude"].values, data["decimalLongitude"].values
    )
    return data

# Client selection priority:
#   1. GITHUB_PAT        -> GitHub Models (gpt-4o-mini)
#   2. ANTHROPIC_API_KEY -> Anthropic (claude-haiku)
_chat_client = None
try:
    if os.environ.get("GITHUB_PAT"):
        _chat_client = ChatGithub(model="gpt-4o-mini")
    elif os.environ.get("ANTHROPIC_API_KEY"):
        _chat_client = ChatAnthropic(model="claude-haiku-4-5-20251001")
    else:
        print(
            "Warning: No LLM API key found. Set GITHUB_PAT or ANTHROPIC_API_KEY in .env to enable AI Explorer."
        )
except Exception as e:
    print(
        f"Warning: Could not initialize AI client ({e}). AI Explorer will be disabled."
    )

_greeting = open(os.path.join(os.path.dirname(__file__), "greeting.md")).read()
qc = (
    QueryChat(df_full, "beetles", client=_chat_client, greeting=_greeting)
    if _chat_client is not None
    else None
)

app_ui = ui.page_navbar(
    ui.nav_panel(
        "Dashboard",
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
                            ui.output_ui("plot_timeseries"),
                            full_screen=True,
                        ),
                        ui.card(
                            ui.card_header("Basis of Record"),
                            ui.output_ui("plot_basis"),
                            full_screen=True,
                        ),
                        col_widths=[6, 6],
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("Top Rights Holders"),
                            ui.output_ui("plot_rights_holder"),
                            full_screen=True,
                        ),
                        ui.card(
                            ui.card_header("Seasonal Observations by Month"),
                            ui.output_ui("plot_monthly"),
                            full_screen=True,
                        ),
                        col_widths=[6, 6],
                    ),
                ),
                open=True,
            ),
        ),
    ),
    ui.nav_panel(
        "AI Explorer",
        ui.layout_sidebar(
            (
                qc.sidebar()
                if qc is not None
                else ui.sidebar(
                    ui.p(
                        "AI Explorer is disabled. Set GITHUB_PAT or ANTHROPIC_API_KEY "
                        "in your .env file and restart the app to enable it.",
                        style="color: #b71c1c;",
                    )
                )
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Occurrences Over Time (AI Filtered)"),
                    ui.output_ui("ai_plot_timeseries"),
                ),
                ui.card(
                    ui.card_header("Basis of Record (AI Filtered)"),
                    ui.output_ui("ai_plot_basis"),
                ),
                col_widths=[6, 6],
            ),
            ui.card(
                ui.card_header(
                    ui.div(
                        "Filtered Data",
                        ui.download_button(
                            "download_csv",
                            "Download CSV",
                            class_="btn-success btn-sm",
                        ),
                        style="display: flex; justify-content: space-between; align-items: center; width: 100%;",
                    ),
                ),
                ui.output_data_frame("ai_table") if qc is not None else ui.p(""),
                full_screen=True,
            ),
        ),
    ),  # closes ui.nav_panel("AI Explorer")
    title="Japanese Beetle Tracker",
    header=ui.tags.style(
        """
        body { background-color: #e8f5e9; }
        .sidebar { background-color: #c8e6c9; }
        .card { background-color: #f1f8e9; }
        .card-header { background-color: #a5d6a7; color: #1b5e20; }
        .value-box { background-color: #c8e6c9 !important; }
    """
    ),
)


def server(input, output, session):
    if qc is not None:
        sv = qc.server()

        @render.data_frame
        def ai_table():
            return sv.df()

        @render.ui
        def ai_plot_timeseries():
            counts = sv.df().groupby("year").size().reset_index(name="count")
            nearest = alt.selection_point(
                nearest=True, on="mouseover", fields=["year"], empty=False
            )
            line = (
                alt.Chart(counts)
                .mark_line(color="#2e7d32")
                .encode(
                    x=alt.X(
                        "year:Q", title="Year", axis=alt.Axis(tickCount=6, format="d")
                    ),
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
            html = (line + points).properties(width="container", height=300).to_html()
            return ui.tags.iframe(srcdoc=html, width="100%", height="320px", style="border:none")

        @render.ui
        def ai_plot_basis():
            counts = sv.df()["basisOfRecord"].dropna().value_counts().reset_index()
            counts.columns = ["basisOfRecord", "count"]

            html = (
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
                .to_html()
            )
            return ui.tags.iframe(srcdoc=html, width="100%", height="370px", style="border:none")

    @reactive.calc
    def filtered_expr():
        year_min, year_max = input.year_range()

        expr = beetle_df.filter(_.year.between(year_min, year_max))

        if input.region() != "All":
            expr = expr.filter(_.countryCode == input.region())

        if input.basis_record() != "All":
            expr = expr.filter(_.basisOfRecord == input.basis_record())

        return expr

    # Build the point dataset used to draw the map; always resolution 2 to match CELL_LOCATIONS.
    @reactive.calc
    def map_points_df():
        pts = (
            filtered_expr()
            .select(["decimalLatitude", "decimalLongitude"])
            .filter(
                _.decimalLatitude.notnull()
                & _.decimalLongitude.notnull()
                & _.decimalLatitude.between(-90, 90)
                & _.decimalLongitude.between(-180, 180)
            )
            .execute()
        )
        if pts.empty:
            return pts.assign(cell=pd.Series(dtype="object"))
        return add_h3_cells(pts, 2)

    @reactive.calc
    def filtered_df():
        return filtered_expr().execute()

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
        if input.region() == "All":
            region_label = "Status Worldwide"
        else:
            country = pycountry.countries.get(alpha_2=input.region())
            region_name = country.name if country is not None else input.region()
            region_label = f"Status in {region_name}"
        return ui.value_box(f"{region_label} as of {year_max}", value)

    # Line chart: number of observations per year across the filtered dataset
    @render.ui
    def plot_timeseries():
        counts = filtered_df().groupby("year").size().reset_index(name="count")
        counts = counts.dropna(subset=["year"])
        counts["year"] = counts["year"].astype(int)

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

        html = (line + points).properties(width="container", height=300).to_html()
        return ui.tags.iframe(srcdoc=html, width="100%", height="320px", style="border:none")

    # Pie chart: share of each basisOfRecord category in the filtered dataset
    @render.ui
    def plot_basis():
        counts = filtered_df()["basisOfRecord"].value_counts().reset_index()
        counts.columns = ["basisOfRecord", "count"]
        html = (
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
            .to_html()
        )
        return ui.tags.iframe(srcdoc=html, width="100%", height="370px", style="border:none")

    # Bar chart: top 10 rights holders
    @render.ui
    def plot_rights_holder():
        counts = (
            filtered_df()["rightsHolder"].dropna().value_counts().head(10).reset_index()
        )
        counts.columns = ["rightsHolder", "count"]
        html = (
            alt.Chart(counts)
            .mark_bar()
            .encode(
                x=alt.X("count:Q", title="Observations"),
                y=alt.Y("rightsHolder:N", sort="-x", title="Rights Holder"),
                tooltip=["rightsHolder", "count"],
            )
            .properties(width="container", height=300)
            .to_html()
        )
        return ui.tags.iframe(srcdoc=html, width="100%", height="320px", style="border:none")

    @render.ui
    def plot_monthly():
        monthly = (
            filtered_df()
            .assign(
                month=pd.to_datetime(
                    filtered_df()["eventDate"],
                    errors="coerce",
                    utc=True,
                    format="mixed",
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

        html = (
            alt.Chart(monthly)
            .mark_bar()
            .encode(
                x=alt.X(
                    "month:O",
                    title="Month",
                    axis=alt.Axis(
                        labelExpr="{'1':'Jan','2':'Feb','3':'Mar','4':'Apr','5':'May',"
                        "'6':'Jun','7':'Jul','8':'Aug','9':'Sep','10':'Oct',"
                        "'11':'Nov','12':'Dec'}[datum.label]"
                    ),
                ),
                y=alt.Y("count:Q", title="Observations"),
                tooltip=["month_name", "count"],
            )
            .properties(width="container", height=300)
            .to_html()
        )
        return ui.tags.iframe(srcdoc=html, width="100%", height="320px", style="border:none")

    # Create the map and all Polygon widgets once per session.
    # Reactive effects will mutate polygon properties instead of recreating the map.
    _m = Map(
        center=(20, 0),
        zoom=2,
        basemap={"url": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", "max_zoom": 19, "attribution": "CartoDB Positron"},
        layout={"height": "450px"},
    )
    _cell_polygons: dict = {}
    for _cell, _locations in CELL_LOCATIONS.items():
        _poly = Polygon(
            locations=_locations,
            color="#000",
            fill_color="#000",
            fill_opacity=0.0,
            weight=0,
        )
        _m.add_layer(_poly)
        _cell_polygons[_cell] = _poly

    # HTML widget for the legend — added to the map once, content updated reactively
    _legend_html = widgets.HTML("")
    _m.add_control(WidgetControl(widget=_legend_html, position="bottomleft"))

    def _update_polygons():
        pts = map_points_df()

        if pts.empty:
            for poly in _cell_polygons.values():
                poly.fill_opacity = 0.0
                poly.weight = 0
            _legend_html.value = ""
            return
        counts = pts["cell"].value_counts()
        max_count = counts.max()
        cmap = cm.get_cmap(input.colormap())
        for cell, poly in _cell_polygons.items():
            if cell in counts.index:
                color = mcolors.to_hex(cmap(counts[cell] / max_count))
                poly.color = color
                poly.fill_color = color
                poly.fill_opacity = 0.7
                poly.weight = 1
            else:
                poly.fill_opacity = 0.0
                poly.weight = 0

        legend_steps = ["Very Low", "Low", "Medium", "High", "Very High"]
        step_values = [max(1, round(max_count * i / 4)) for i in range(5)]
        items = "".join(
            f'<div style="display:flex;align-items:center;margin:2px 0">'
            f'<span style="width:14px;height:14px;background:{mcolors.to_hex(cmap(i/4))};'
            f'display:inline-block;margin-right:6px;border-radius:2px"></span>'
            f'<span>{label} ({step_values[i]:,}{"–"+f"{step_values[i+1]:,}" if i < 4 else ""})</span></div>'
            for i, label in enumerate(legend_steps)
        )
        _legend_html.value = (
            f'<div style="background:white;padding:8px 10px;border-radius:4px;'
            f'font-size:0.82em;box-shadow:0 1px 4px rgba(0,0,0,0.25)">'
            f'<b style="display:block;margin-bottom:4px">Observations</b>{items}</div>'
        )

    @render_widget
    def map():
        return _m

    @reactive.effect
    def _on_filters_changed():
        _update_polygons()

    # reset button
    @reactive.effect
    @reactive.event(input.reset_btn)
    def reset_filters():
        ui.update_slider("year_range", value=[YEAR_MIN, YEAR_MAX])
        ui.update_selectize("region", selected="All")
        ui.update_radio_buttons("basis_record", selected="All")

    @render.download(filename="beetle_data.csv")
    def download_csv():
        with io.StringIO() as buf:
            sv.df().to_csv(buf, index=False)
            yield buf.getvalue()


app = App(app_ui, server, static_assets=os.path.join(os.path.dirname(__file__), "www"))
