#!/usr/bin/env python3
"""
Generate isochrones for all Czech regional capitals using OpenRouteService API.
Based on the original isochrones_from_position.py script.
"""

import requests
import folium
import pandas as pd
import gpxpy
import gpxpy.gpx
from pathlib import Path
import time
import config

# Load regional capitals from CSV
CITIES_CSV = Path(__file__).parent / "krajska_mista.csv"
ISOCHRONES_DIR = Path(__file__).parent / "isochrones"
ISOCHRONES_DIR.mkdir(exist_ok=True)

# Time interval - 1 hour (max allowed by ORS)
TIME_INTERVAL = 3600  # seconds

# Headers for OpenRouteService API
HEADERS = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    'Authorization': config.ORS_API_KEY,
    'Content-Type': 'application/json; charset=utf-8'
}


def generate_isochrone_for_city(city_data: dict) -> None:
    """Generate isochrone for a single city and save as GPX + GeoJSON."""
    city = city_data['city']
    coordinates = [float(city_data['lon']), float(city_data['lat'])]

    # Create request body
    body = {
        "locations": [coordinates],
        "range": [TIME_INTERVAL],
        "range_type": "time"
    }

    # Make API request
    response = requests.post(
        'https://api.openrouteservice.org/v2/isochrones/driving-car',
        json=body,
        headers=HEADERS
    )

    if response.status_code != 200:
        print(f"ERROR: Failed to retrieve isochrone for {city}. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return

    print(f"✓ Isochrone data for {city} retrieved successfully.")
    isochrone_data = response.json()

    # Save as GeoJSON
    geojson_file = ISOCHRONES_DIR / f"isochrone_{city}.geojson"
    with open(geojson_file, 'w') as f:
        import json
        json.dump(isochrone_data, f)
    print(f"  Saved GeoJSON: {geojson_file}")

    # Convert to GPX
    feature = isochrone_data['features'][0]
    geometry = feature['geometry']
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    if geometry['type'] == 'Polygon':
        for lon, lat in geometry['coordinates'][0]:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    elif geometry['type'] == 'MultiPolygon':
        for polygon in geometry['coordinates']:
            for lon, lat in polygon[0]:
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

    gpx_filename = ISOCHRONES_DIR / f"isochrone_{city}.gpx"
    with open(gpx_filename, 'w') as f:
        f.write(gpx.to_xml())
    print(f"  Saved GPX: {gpx_filename}")


def create_combined_map() -> None:
    """Create a combined Folium map with all isochrones."""
    # Load all cities
    df = pd.read_csv(CITIES_CSV)

    # Center map on Czech Republic
    center_lat = df['lat'].mean()
    center_lon = df['lon'].mean()

    isochrone_map = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    for _, row in df.iterrows():
        city = row['city']
        geojson_file = ISOCHRONES_DIR / f"isochrone_{city}.geojson"

        if not geojson_file.exists():
            continue

        with open(geojson_file) as f:
            import json
            data = json.load(f)

        # Add isochrone layer
        folium.GeoJson(
            data,
            name=f'{city} (1h)',
            style_function=lambda feature, c=city: {
                'fillColor': '#3186cc',
                'color': '#3186cc',
                'weight': 1,
                'fillOpacity': 0.2,
            },
            tooltip=f'Isochrone from {city}'
        ).add_to(isochrone_map)

        # Add marker for city center
        folium.Marker(
            [row['lat'], row['lon']],
            popup=city,
            icon=folium.Icon(color='red', icon='star')
        ).add_to(isochrone_map)

    folium.LayerControl().add_to(isochrone_map)

    output_file = Path(__file__).parent / "all_isochrones_map.html"
    isochrone_map.save(output_file)
    print(f"\nCombined map saved to: {output_file}")


def main():
    print("=" * 60)
    print("Generating isochrones for all Czech regional capitals")
    print("Time interval: 1 hour (3600 seconds)")
    print("=" * 60)

    df = pd.read_csv(CITIES_CSV)

    for i, (_, row) in enumerate(df.iterrows()):
        print(f"\nProcessing: {row['city']} ({i+1}/{len(df)})")
        generate_isochrone_for_city(row)
        # Add delay between requests to avoid rate limiting
        if i < len(df) - 1:
            time.sleep(2)  # 2 second delay between requests

    print("\n" + "=" * 60)
    print("Creating combined map...")
    create_combined_map()
    print("Done!")


if __name__ == "__main__":
    main()
