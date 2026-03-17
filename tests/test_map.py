from shiny import App, ui, reactive
from shinywidgets import render_widget, output_widget
from ipyleaflet import Map, Polygon
import h3
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import ibis
import os
from ibis import _

PARQUET_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "gbif-beetle.parquet")
con = ibis.duckdb.connect()
beetle_df = con.read_parquet(PARQUET_PATH)

# --- Pre-processing at startup (data only, no widgets) ---

pts_all = (
    beetle_df
    .select(["decimalLatitude", "decimalLongitude", "year"])
    .filter(
        _.decimalLatitude.notnull()
        & _.decimalLongitude.notnull()
        & _.decimalLatitude.between(-90, 90)
        & _.decimalLongitude.between(-180, 180)
        & _.year.notnull()
    )
    .execute()
)

YEAR_MIN = int(pts_all["year"].min())
YEAR_MAX = int(pts_all["year"].max())

fn = np.vectorize(lambda lat, lng: h3.latlng_to_cell(lat, lng, 2))
pts_all["cell"] = fn(pts_all["decimalLatitude"].values, pts_all["decimalLongitude"].values)

agg = pts_all.groupby(["cell", "year"])["decimalLatitude"].count().reset_index(name="count")

# Pre-compute cell boundary coords (plain data, not widgets)
cell_locations: dict[str, list] = {}
for cell in agg["cell"].unique():
    boundary = h3.cell_to_boundary(cell)  # [(lat, lng), ...]
    cell_locations[cell] = [(lat, lng) for lat, lng in boundary]

cmap = cm.get_cmap("plasma")
print(f"[startup] {len(pts_all)} pts | {len(cell_locations)} cells")


app_ui = ui.page_fluid(
    ui.input_slider("year_range", "Year Range", min=YEAR_MIN, max=YEAR_MAX, value=[YEAR_MIN, YEAR_MAX], sep=""),
    output_widget("map"),
)


def server(input, output, session):
    m = Map(center=(20, 0), zoom=2, layout={"height": "500px"})

    # Create Polygon widgets inside the session, add all to m once
    cell_polygons: dict[str, Polygon] = {}
    for cell, locations in cell_locations.items():
        poly = Polygon(locations=locations, color="#000", fill_color="#000", fill_opacity=0.0, weight=0)
        m.add_layer(poly)
        cell_polygons[cell] = poly

    def update_polygons(year_min, year_max):
        counts = (
            agg.loc[agg["year"].between(year_min, year_max)]
            .groupby("cell")["count"].sum()
        )
        max_count = counts.max() if not counts.empty else 1
        visible = 0
        for cell, poly in cell_polygons.items():
            if cell in counts.index:
                color = mcolors.to_hex(cmap(counts[cell] / max_count))
                poly.color = color
                poly.fill_color = color
                poly.fill_opacity = 0.7
                poly.weight = 1
                visible += 1
            else:
                poly.fill_opacity = 0.0
                poly.weight = 0
        print(f"[update_polygons] {year_min}-{year_max}: {visible} visible cells")

    update_polygons(YEAR_MIN, YEAR_MAX)

    @render_widget
    def map():
        return m

    @reactive.effect
    @reactive.event(input.year_range)
    def update_hex_layer():
        year_min, year_max = input.year_range()
        update_polygons(year_min, year_max)


app = App(app_ui, server)
