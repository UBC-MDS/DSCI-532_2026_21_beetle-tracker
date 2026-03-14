from shiny import App, ui, reactive, render
from shinywidgets import render_widget, output_widget, render_altair
from querychat import QueryChat
from chatlas import ChatAnthropic, ChatGithub
from ipyleaflet import Map, basemaps, GeoJSON, LegendControl, WidgetControl
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
REGIONS = ["All"] + (
    beetle_df.filter(_.countryCode.notnull())
    .select("countryCode")
    .distinct()
    .order_by("countryCode")
    .execute()["countryCode"]
    .tolist()
)
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

# Available map underlays; keys are displayed in the sidebar dropdown
BASEMAP_OPTIONS = {
    "CartoDB Positron": basemaps.CartoDB.Positron,  # clean light gray, minimal labels
    "CartoDB Dark Matter": basemaps.CartoDB.DarkMatter,  # dark version of Positron
    "Esri Gray Canvas": basemaps.Esri.WorldGrayCanvas,  # very minimal, nearly label-free
    "Esri Topo": basemaps.Esri.WorldTopoMap,  # terrain and topographic detail
    "Satellite": basemaps.Esri.WorldImagery,  # aerial/satellite imagery
}

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
                    output_widget("ai_plot_timeseries"),
                ),
                ui.card(
                    ui.card_header("Basis of Record (AI Filtered)"),
                    output_widget("ai_plot_basis"),
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

        @render_altair
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
            return (line + points).properties(width="container", height=300)

        @render_altair
        def ai_plot_basis():
            counts = sv.df()["basisOfRecord"].dropna().value_counts().reset_index()
            counts.columns = ["basisOfRecord", "count"]

            return (
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

    @reactive.calc
    def filtered_expr():
        year_min, year_max = input.year_range()

        expr = beetle_df.filter(_.year.between(year_min, year_max))

        if input.region() != "All":
            expr = expr.filter(_.countryCode == input.region())

        if input.basis_record() != "All":
            expr = expr.filter(_.basisOfRecord == input.basis_record())

        return expr

    # Value box: count of rows in the filtered dataset
    @render.ui
    def vb_total_obs():
        count = filtered_expr().count().execute()
        return ui.value_box("Total Observations", f"{count:,}")

    # Value box: earliest year with an observation in the filtered dataset
    @render.ui
    def vb_first_recorded():
        result = filtered_expr()["year"].min().execute()
        value = (
            str(int(result)) if result is not None and not pd.isna(result) else "N/A"
        )
        return ui.value_box("First Recorded", value)

    # Value box: whether any observation exists in the slider's max year
    @render.ui
    def vb_status():
        year_min, year_max = input.year_range()
        present = filtered_expr().filter(_.year == year_max).count().execute() > 0
        value = "Present" if present else "Not Detected"
        return ui.value_box(f"Status in Region as of {year_max}", value)

    # Line chart: number of observations per year across the filtered dataset
    @render_altair
    def plot_timeseries():
        counts = (
            filtered_expr()
            .filter(_.year.notnull())
            .group_by("year")
            .aggregate(count=_.year.count())
            .order_by("year")
            .execute()
        )
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

        chart = (line + points).properties(width="container", height=300)
        return chart

    # Pie chart: share of each basisOfRecord category in the filtered dataset
    @render_altair
    def plot_basis():
        counts = (
            filtered_expr()
            .group_by("basisOfRecord")
            .aggregate(count=_.basisOfRecord.count())
            .execute()
            .dropna(subset=["basisOfRecord"])
        )
        return (
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

    # Bar chart: top 10 rights holders
    @render_altair
    def plot_rights_holder():
        counts = (
            filtered_expr()
            .filter(_.rightsHolder.notnull())
            .group_by("rightsHolder")
            .aggregate(count=_.rightsHolder.count())
            .order_by(ibis.desc("count"))
            .limit(10)
            .execute()
        )
        return (
            alt.Chart(counts)
            .mark_bar()
            .encode(
                x=alt.X("count:Q", title="Observations"),
                y=alt.Y("rightsHolder:N", sort="-x", title="Rights Holder"),
                tooltip=["rightsHolder", "count"],
            )
            .properties(width="container", height=300)
        )

    @render_altair
    def plot_monthly():
        monthly = (
            filtered_expr()
            .filter(_.eventDate.notnull())
            .filter(_.eventDate.length() >= 7)
            .mutate(
                month=_.eventDate.re_extract(r"^\d{4}-(\d{2})", 1).cast("int")
            )  # regex (claude suggestion)
            .filter(_.month.between(1, 12))
            .group_by("month")
            .aggregate(count=_.month.count())
            .order_by("month")
            .execute()
        )
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

        return (
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
        )

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
        m = Map(
            center=(20, 0),
            zoom=2,
            basemap=BASEMAP_OPTIONS[input.basemap()],
            layout={"height": "450px"},
        )

        # Drop rows with missing coordinates and clamp to valid lat/lon ranges
        pts = (
            filtered_expr()
            .select(["decimalLatitude", "decimalLongitude", "stateProvince"])
            .filter(
                _.decimalLatitude.notnull()
                & _.decimalLongitude.notnull()
                & _.decimalLatitude.between(-90, 90)
                & _.decimalLongitude.between(-180, 180)
            )
            .execute()
        )

        # Return a plain empty map if the current filter selection has no data
        if pts.empty:
            return m

        # --- H3 hexagonal binning ---
        # Resolution adapts to the number of points so the GeoJSON payload stays manageable:
        # large datasets use resolution 2 (~5,882 global cells) to avoid browser timeouts,
        # while smaller datasets use resolution 3 (~41,163 cells) for finer detail.
        resolution = 2 if len(pts) > 5_000 else 3
        latlng_to_cell = np.vectorize(
            lambda lat, lng: h3.latlng_to_cell(lat, lng, resolution)
        )
        pts = pts.copy()
        pts["cell"] = latlng_to_cell(
            pts["decimalLatitude"].values, pts["decimalLongitude"].values
        )

        # Count observations per cell; most-frequent cells will receive the darkest color
        counts = pts["cell"].value_counts()

        # Top 5 stateProvinces by count within each cell for the hover tooltip
        top_locations = (
            pts.dropna(subset=["stateProvince"])
            .groupby(["cell", "stateProvince"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
            .groupby("cell")
            .head(5)
            .groupby("cell")
            .apply(lambda g: g[["stateProvince", "n"]].values.tolist())
            .to_dict()
        )

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
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [coords]},
                    "properties": {
                        "count": int(count),
                        "top_locations": [
                            [str(name), int(n)]
                            for name, n in top_locations.get(cell, [])
                        ],
                        "style": {
                            "color": color,  # border color
                            "fillColor": color,  # fill color
                            "fillOpacity": 0.7,
                            "weight": 0.3,  # border thickness
                        },
                    },
                }
            )

        # Hover info box in the top-right corner
        hover_html = widgets.HTML(
            "<div style='padding:6px 10px'>Hover over a cell</div>"
        )
        m.add_control(WidgetControl(widget=hover_html, position="topright"))

        # Add the hex bin layer; style_callback applies the per-feature color stored above
        geojson_layer = GeoJSON(
            data={"type": "FeatureCollection", "features": features},
            style_callback=lambda f: f["properties"]["style"],
            hover_style={"fillOpacity": 0.95, "weight": 1.5},
        )

        def on_hover(feature, **kwargs):
            props = feature["properties"]
            rows = "".join(
                f"<tr><td>{name}</td><td style='text-align:right;padding-left:12px'>{n:,}</td></tr>"
                for name, n in props["top_locations"]
            )
            hover_html.value = f"""
                <div style='padding:6px 10px;min-width:160px;background:white;border-radius:4px'>
                    <b>{props['count']:,} observations</b>
                    <table style='margin-top:4px;width:100%;font-size:0.9em'>
                        <tr><th style='text-align:left'>Location</th><th>Count</th></tr>
                        {rows}
                    </table>
                    <div style='font-size:0.8em;color:#888;margin-top:4px'>Showing top 5 locations only</div>
                </div>
            """

        geojson_layer.on_hover(on_hover)
        m.add_layer(geojson_layer)

        # --- Legend ---
        # 5 evenly-spaced steps spanning the actual count range in the current filtered data
        legend_steps = ["Very Low", "Low", "Medium", "High", "Very High"]
        legend_colors = {
            f"{label} ({max(1, round(max_count * i / 4)):,})": mcolors.to_hex(
                cmap(i / 4)
            )
            for i, label in enumerate(legend_steps)
        }
        m.add_control(
            LegendControl(legend_colors, title="Observations", position="bottomleft")
        )

        return m

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
