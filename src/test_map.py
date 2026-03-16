from shiny import App, ui, reactive
from shinywidgets import render_widget, output_widget
from ipyleaflet import Map, GeoJSON, WidgetControl
import ipywidgets as widgets
import h3
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import pandas as pd
import ibis
import os
from ibis import _

PARQUET_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "gbif-beetle.parquet")
con = ibis.duckdb.connect()
beetle_df = con.read_parquet(PARQUET_PATH)

_meta = beetle_df.aggregate(year_min=beetle_df["year"].min(), year_max=beetle_df["year"].max()).execute()
YEAR_MIN = int(_meta["year_min"].iloc[0])
YEAR_MAX = int(_meta["year_max"].iloc[0])


def add_h3_cells(data: pd.DataFrame, resolution: int) -> pd.DataFrame:
    data = data.copy()
    latlng_to_cell = np.vectorize(lambda lat, lng: h3.latlng_to_cell(lat, lng, resolution))
    data["cell"] = latlng_to_cell(data["decimalLatitude"].values, data["decimalLongitude"].values)
    return data


def build_geojson_features(pts: pd.DataFrame, cmap) -> list:
    counts = pts["cell"].value_counts()
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
    max_count = counts.max()
    features = []
    for cell, count in counts.items():
        boundary = h3.cell_to_boundary(cell)
        coords = [[lng, lat] for lat, lng in boundary]
        coords.append(coords[0])
        color = mcolors.to_hex(cmap(count / max_count))
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {
                "count": int(count),
                "cell": cell,
                "top_locations": [[str(name), int(n)] for name, n in top_locations.get(cell, [])],
                "style": {"color": color, "fillColor": color, "fillOpacity": 0.7, "weight": 0.3},
            },
        })
    return features


app_ui = ui.page_fluid(
    ui.input_slider("year_range", "Year Range", min=YEAR_MIN, max=YEAR_MAX, value=[YEAR_MIN, YEAR_MAX], sep=""),
    output_widget("map"),
)


def server(input, output, session):
    # Create the map once — never recreated
    m = Map(center=(20, 0), zoom=2, layout={"height": "500px"})
    hover_html = widgets.HTML("<div style='padding:6px 10px'>Hover over a cell</div>")
    m.add_control(WidgetControl(widget=hover_html, position="topright"))

    current_layer = [None]  # plain list used as a mutable cell, avoids reactive loops

    @render_widget
    def map():
        return m

    @reactive.effect
    def update_hex_layer():
        year_min, year_max = input.year_range()

        pts = (
            beetle_df
            .filter(_.year.between(year_min, year_max))
            .select(["decimalLatitude", "decimalLongitude", "stateProvince"])
            .filter(
                _.decimalLatitude.notnull()
                & _.decimalLongitude.notnull()
                & _.decimalLatitude.between(-90, 90)
                & _.decimalLongitude.between(-180, 180)
            )
            .execute()
        )

        # Remove the previous GeoJSON layer if one exists
        if current_layer[0] is not None:
            m.remove_layer(current_layer[0])
            current_layer[0] = None

        if pts.empty:
            return

        resolution = 2 if len(pts) > 5_000 else 3
        pts = add_h3_cells(pts, resolution)

        cmap = cm.get_cmap("plasma")
        features = build_geojson_features(pts, cmap)

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
                </div>
            """

        geojson_layer.on_hover(on_hover)
        m.add_layer(geojson_layer)
        current_layer[0] = geojson_layer


app = App(app_ui, server)
