#!/usr/bin/env python3
"""
Generate 30-minute isochrones for all Czech districts (okresy).
Calculate statistics (min/mean/max darkness) within each isochrone.
"""

import requests
import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
import time
import config
from publish_html import save_html_for_pages, nav_links_html

# Paths
OKRES_CSV = Path(__file__).parent / "okresni_mesta.csv"
ISOCHRONES_OKRES_DIR = Path(__file__).parent / "isochrones_okres"
OUTPUT_DIR = Path(__file__).parent / "output"
VIEWPOINTS_CSV = OUTPUT_DIR / "viewpoints_with_darkness.csv"

ISOCHRONES_OKRES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Time interval - 30 minutes
TIME_INTERVAL = 1800  # seconds

HEADERS = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    'Authorization': config.ORS_API_KEY,
    'Content-Type': 'application/json; charset=utf-8'
}


def generate_isochrone_for_city(city_data: dict) -> dict | None:
    """Generate isochrone for a single district and return stats."""
    okres = city_data['okres']
    kraj = city_data['kraj']
    coordinates = [float(city_data['longitude']), float(city_data['latitude'])]

    body = {
        "locations": [coordinates],
        "range": [TIME_INTERVAL],
        "range_type": "time"
    }

    response = requests.post(
        'https://api.openrouteservice.org/v2/isochrones/driving-car',
        json=body,
        headers=HEADERS
    )

    if response.status_code != 200:
        print(f"  ERROR: {okres} - Status {response.status_code}")
        return None

    isochrone_data = response.json()
    feature = isochrone_data['features'][0]
    geometry = feature['geometry']

    # Save GeoJSON
    geojson_file = ISOCHRONES_OKRES_DIR / f"isochrone_{okres}.geojson"
    with open(geojson_file, 'w') as f:
        json.dump(isochrone_data, f)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features([feature], crs="EPSG:4326")

    # Load viewpoints and find those within isochrone
    viewpoints = pd.read_csv(VIEWPOINTS_CSV)
    viewpoint_gdf = gpd.GeoDataFrame(
        viewpoints,
        geometry=gpd.points_from_xy(viewpoints['lon'], viewpoints['lat']),
        crs="EPSG:4326"
    )

    # Spatial join to find points within isochrone
    joined = gpd.sjoin(viewpoint_gdf, gdf, how='inner', predicate='within')

    # Calculate statistics
    darkness_values = joined['darkness_value'].dropna()

    if len(darkness_values) > 0:
        stats = {
            'okres': okres,
            'kraj': kraj,
            'lat': coordinates[1],
            'lon': coordinates[0],
            'count': len(darkness_values),
            'min_darkness': darkness_values.min(),
            'mean_darkness': darkness_values.mean(),
            'max_darkness': darkness_values.max(),
        }
    else:
        stats = {
            'okres': okres,
            'kraj': kraj,
            'lat': coordinates[1],
            'lon': coordinates[0],
            'count': 0,
            'min_darkness': None,
            'mean_darkness': None,
            'max_darkness': None,
        }

    print(f"  ✓ {okres}: {stats['count']} bodů, tma: {stats['min_darkness']:.4f} - {stats['max_darkness']:.4f}")
    return stats


def main():
    print("=" * 60)
    print("Generating 30-min isochrones for all Czech districts")
    print("=" * 60)

    df = pd.read_csv(OKRES_CSV)
    all_stats = []

    for i, (_, row) in enumerate(df.iterrows()):
        print(f"\n[{i+1}/{len(df)}] Processing: {row['okres']} ({row['kraj']})")
        stats = generate_isochrone_for_city(row)
        if stats:
            all_stats.append(stats)
        # Delay to avoid rate limiting
        if i < len(df) - 1:
            time.sleep(2)

    # Save statistics
    stats_df = pd.DataFrame(all_stats)
    stats_output = OUTPUT_DIR / "okres_statistics.csv"
    stats_df.to_csv(stats_output, index=False)
    print(f"\nSaved statistics to: {stats_output}")

    # Create summary map
    create_summary_map(stats_df)


def create_summary_map(stats_df):
    """Create a map showing all district centers with stats in popup."""
    import folium

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap', control_scale=True)

    for _, row in stats_df.iterrows():
        if row['count'] == 0:
            continue

        popup_text = f"""
        <b>{row['okres']}</b> ({row['kraj']})<br>
        Bodů: {row['count']}<br>
        Min tma: {row['min_darkness']:.4f}<br>
        Průměr: {row['mean_darkness']:.4f}<br>
        Max tma: {row['max_darkness']:.4f}
        """

        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['okres']}: {row['count']} bodů"
        ).add_to(m)

    m.get_root().html.add_child(
        folium.Element(nav_links_html([
            ("GitHub", "https://github.com/jarogumulec/perseidy"),
            ("Regional", "perseidy_regional.html"),
        ]))
    )

    output_file = OUTPUT_DIR / "okres_isochrones_map.html"
    saved_file, docs_file = save_html_for_pages(m, output_file)
    print(f"Saved summary map to: {saved_file}")
    print(f"Mirrored to: {docs_file}")


if __name__ == "__main__":
    main()
