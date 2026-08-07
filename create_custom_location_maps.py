#!/usr/bin/env python3
"""
Create interactive HTML maps for custom locations (Brno center, Koprivnice) with isochrones.
Shows only viewpoints WITHIN the 1h isochrone (similar to regional map logic).
"""

import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
import folium
from publish_html import save_html_for_pages, nav_links_html, ratio_legend_html

# Paths
OUTPUT_DIR = Path(__file__).parent / "output"
VIEWPOINTS_CSV = Path(__file__).parent / "output/viewpoints_with_darkness.csv"
ISOCHRONES_DIR = Path(__file__).parent / "isochrones"

FALCHI_PNG = Path(__file__).parent / "output/falchi_overlay.png"
FALCHI_BOUNDS_JSON = Path(__file__).parent / "output/falchi_bounds.json"

# Falchi data with μcd/m² as primary unit (extended to orange)
FALCHI_DATA = [
    (0.01, "<1.74", "#000000"),
    (0.02, "1.74–3.48", "#808080"),
    (0.04, "3.48–6.96", "#A9A9A9"),
    (0.08, "6.96–13.9", "#00008B"),
    (0.16, "13.9–27.8", "#0000FF"),
    (0.32, "27.8–55.7", "#444AF8"),
    (0.64, "55.7–111", "#006400"),
    (1.28, "111–223", "#008000"),
    (2.56, "223–445", "#FFFF00"),
]

# Custom locations with multiple time intervals
LOCATIONS = {
    "brno": {
        "display": "Centrum Brna",
        "coords": [49.2026006, 16.6106008],
        "intervals": [15, 30, 45, 60]
    },
    "koprivnice": {
        "display": "Kopřivnice",
        "coords": [49.5887553, 18.1351564],
        "intervals": [15, 30, 45, 60]
    }
}

# Isochrone colors
ISOCHROME_COLORS = {
    15: '#4CAF50',
    30: '#2196F3',
    45: '#FF9800',
    60: '#F44336'
}


def get_falchi_color(value):
    if pd.isna(value):
        return '#888888'
    for threshold, _, color in FALCHI_DATA:
        if value <= threshold:
            return color
    return '#FFFF00'


def get_falchi_category(value):
    if pd.isna(value):
        return "Neznámá"
    thresholds = [
        (0.01, "Černá"),
        (0.02, "Šedá"),
        (0.04, "Světle šedá"),
        (0.08, "Tmavě modrá"),
        (0.16, "Modrá"),
        (0.32, "Světle modrá"),
        (0.64, "Zelená"),
        (1.28, "Tmavě zelená"),
        (2.56, "Žlutá"),
    ]
    for thresh, label in thresholds:
        if value <= thresh:
            return label
    return "Světle žlutá"


def add_falchi_layer(m):
    if not FALCHI_PNG.exists() or not FALCHI_BOUNDS_JSON.exists():
        return None

    with open(FALCHI_BOUNDS_JSON) as f:
        bounds_info = json.load(f)

    min_lat, min_lon = bounds_info['min_lat'], bounds_info['min_lon']
    max_lat, max_lon = bounds_info['max_lat'], bounds_info['max_lon']

    overlay = folium.raster_layers.ImageOverlay(
        image=str(FALCHI_PNG),
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=0.6,
        name="Světelné znečištění (Falchi)",
        show=True
    )
    overlay.add_to(m)
    return overlay


def create_location_map(location_key: str) -> None:
    """Create map for a single location with all isochrones."""
    loc = LOCATIONS[location_key]
    display_name = loc['display']
    coords = loc['coords']
    intervals = loc['intervals']

    print(f"Creating map for {display_name}...")

    # Load viewpoints
    df = pd.read_csv(VIEWPOINTS_CSV)
    df = df[(df['lat'] >= 48.5) & (df['lat'] <= 51.2)]
    df = df[(df['lon'] >= 12) & (df['lon'] <= 19)]
    df = df[df['darkness_value'].notna()]

    # Create GeoDataFrame
    gdf_points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['lon'], df['lat']),
        crs="EPSG:4326"
    )

    # Load all isochrones and find points within each
    sites_by_isochrone = {}
    for time_min in intervals:
        iso_file = ISOCHRONES_DIR / f"isochrone_{location_key}_{time_min}min.geojson"
        if iso_file.exists():
            with open(iso_file) as f:
                iso_data = json.load(f)
            iso_gdf = gpd.GeoDataFrame.from_features(iso_data, crs="EPSG:4326")
            joined = gpd.sjoin(gdf_points, iso_gdf, how='inner', predicate='within')
            sites_by_isochrone[time_min] = joined[['name', 'lat', 'lon', 'darkness_value']].copy()
            print(f"  {time_min}min: {len(sites_by_isochrone[time_min])} viewpoints")

    # Create map centered on location
    m = folium.Map(location=coords, zoom_start=10, tiles='cartodb.dark_matter', control_scale=True)

    # Add Falchi overlay
    add_falchi_layer(m)

    # Add isochrone layers with their dark points (only < 0.16 threshold)
    good_thresholds = [0.01, 0.02, 0.04, 0.08, 0.16]
    good_colors = ['#000000', '#808080', '#A9A9A9', '#00008B', '#0000FF']

    for time_min in sorted(intervals, reverse=True):
        iso_file = ISOCHRONES_DIR / f"isochrone_{location_key}_{time_min}min.geojson"
        if not iso_file.exists():
            continue

        with open(iso_file) as f:
            iso_data = json.load(f)

        color = ISOCHROME_COLORS.get(time_min, '#888888')
        show_default = (time_min == 60)

        # Create FeatureGroup for this isochrone + its points
        if time_min == 15:
            label = '< 15 min autem'
        elif time_min == 30:
            label = '< 30 min autem'
        elif time_min == 45:
            label = '< 45 min autem'
        else:
            label = '< 60 min autem'
        group = folium.FeatureGroup(name=label, show=show_default)

        # Add isochrone polygon
        folium.GeoJson(
            iso_data,
            style_function=lambda x, c=color: {
                'fillColor': c,
                'color': c,
                'weight': 2,
                'fillOpacity': 0.25
            },
            tooltip=f'Dojezd < {time_min} minut'
        ).add_to(group)

        # Add dark points within this isochrone only (< 0.16 threshold)
        sites = sites_by_isochrone.get(time_min, pd.DataFrame())
        dark_sites = sites[sites['darkness_value'] < 0.16]

        added_points = set()

        for darkness_thresh, point_color in zip(good_thresholds, good_colors):
            level_sites = dark_sites[dark_sites['darkness_value'] <= darkness_thresh]

            for _, row in level_sites.iterrows():
                point_key = (round(row['lat'], 4), round(row['lon'], 4))
                if point_key in added_points:
                    continue

                val = row.get('darkness_value', None)
                if val is None or pd.isna(val):
                    continue

                name = row.get('name', 'Unnamed POI')
                category = get_falchi_category(val)

                popup_text = f"<b>{name}</b><br>Tma: {val:.4f} ({category})"

                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=5,
                    color=point_color,
                    weight=1.5,
                    fill=True,
                    fill_color=point_color,
                    fill_opacity=0.7,
                    popup=popup_text
                ).add_to(group)

                added_points.add(point_key)

        group.add_to(m)

    total_60 = len(sites_by_isochrone.get(60, pd.DataFrame()))
    dark_60 = len(sites_by_isochrone.get(60, pd.DataFrame())[sites_by_isochrone.get(60, pd.DataFrame())['darkness_value'] < 0.16])
    print(f"  Total: {total_60} viewpoints ({dark_60} dark <0.16) within 1h drive")

    # Layer control stays available but collapsed so it does not dominate mobile screens.
    folium.LayerControl(collapsed=True).add_to(m)

    m.get_root().html.add_child(
        folium.Element(nav_links_html([
            ("GitHub", "https://github.com/jarogumulec/perseidy"),
            ("Regional", "perseidy_regional.html"),
        ]))
    )
    m.get_root().html.add_child(folium.Element(ratio_legend_html("Světelné znečištění oblohy")))

    # Save to output directory
    output_file = OUTPUT_DIR / f"perseidy_{location_key}.html"
    saved_file, docs_file = save_html_for_pages(m, output_file)
    print(f"  Saved: {saved_file}")
    print(f"  Mirrored to: {docs_file}")


def main():
    print("=" * 60)
    print("Generating custom isochrone maps for Brno and Koprivnice")
    print("Showing only viewpoints within isochrones (dark sites <0.16)")
    print("=" * 60)

    for loc_key in LOCATIONS.keys():
        create_location_map(loc_key)

    print("\n" + "=" * 60)
    print("Done! Maps saved to output/")
    print("Default view: 60min isochrone with dark viewpoints")
    print("Use checkbox menu to toggle shorter isochrones")
    print("=" * 60)


if __name__ == "__main__":
    main()
