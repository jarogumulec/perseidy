#!/usr/bin/env python3
"""
Create interactive HTML maps for Perseids project.

Generates 3 map variants:
1. Regional view: Select a region, shows isochrone + viewpoints within it
2. Full CZ view: Entire Czech Republic with all viewpoints, manual exploration
3. Top sites: Table of darkest sites per city with map markers
"""

import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
import folium
import base64

# Paths
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
ISOCHRONES_DIR = Path(__file__).parent / "isochrones"

CESKO_TMA_TIFF = DATA_DIR / "cesko_tma.tif"
FALCHI_PNG = OUTPUT_DIR / "falchi_overlay.png"
VIEWPOINTS_CSV = OUTPUT_DIR / "viewpoints_with_darkness.csv"
BEST_SITES_CSV = OUTPUT_DIR / "best_sites_per_city.csv"
REACHABLE_CSV = OUTPUT_DIR / "reachable_dark_sites.csv"

# Falchi bounds in EPSG:4326 (lat/lon)
FALCHI_BOUNDS = [12.083257, 48.545848, 18.866587, 51.062514]  # [min_lon, min_lat, max_lon, max_lat]

# Falchi color palette (from QGIS export)
FALCHI_COLORS = [
    (0.01, '#000000'),  # Černá
    (0.02, '#808080'),  # Tmavě šedá
    (0.04, '#A9A9A9'),  # Šedá
    (0.08, '#00008B'),  # Tmavě modrá
    (0.16, '#0000FF'),  # Modrá
    (0.32, '#444AF8'),  # Světle modrá
    (0.64, '#006400'),  # Tmavě zelená
    (1.28, '#008000'),  # Zelená
    (2.56, '#FFFF00'),  # Žlutá
    (5.12, '#FFA500'),  # Oranžová
    (10.24, '#FF0000'),  # Červená
    (20.48, '#FF00FF'),  # Purpurová
    (40.96, '#FFC0CB'),  # Růžová
]

# Falchi category labels (used in get_falchi_category function)


def get_falchi_color(value):
    """Get Falchi color for a darkness value."""
    if pd.isna(value):
        return '#888888'
    for threshold, color in FALCHI_COLORS:
        if value <= threshold:
            return color
    return '#FFFFFF'


def get_falchi_category(value):
    """Get Falchi category name for a darkness value."""
    if pd.isna(value):
        return "Neznámá"
    if value <= 0.01:
        return "Přirozená tma"
    elif value <= 0.02:
        return "Velmi tmavá"
    elif value <= 0.04:
        return "Téměř přirozená"
    elif value <= 0.08:
        return "Slabé znečištění"
    elif value <= 0.16:
        return "Mírné znečištění"
    elif value <= 0.32:
        return "Střední znečištění"
    elif value <= 0.64:
        return "Znečištěná"
    elif value <= 1.28:
        return "Silné znečištění"
    elif value <= 2.56:
        return "Velmi silné znečištění"
    elif value <= 5.12:
        return "Extrémní znečištění"
    elif value <= 10.24:
        return "Oběžná zóna"
    elif value <= 20.48:
        return "Totální světlo"
    elif value <= 40.96:
        return "Bez oblohy"
    else:
        return "Totální znečištění"


def create_base_map(center_lat=49.8, center_lon=15.5, zoom=7):
    """Create a base Folium map with common settings."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles='OpenStreetMap')
    return m


def add_viewpoint_layer(m, df, title="Výhledová místa"):
    """Add viewpoint markers to the map."""
    for _, row in df.iterrows():
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val):
            continue

        color = get_falchi_color(val)
        category = get_falchi_category(val)
        name = row.get('name', 'Unnamed POI')
        lat, lon = row['lat'], row['lon']

        popup_text = f"<b>{name}</b><br>Tma: {val:.4f}<br>{category}"

        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color='#333333',
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=250)
        ).add_to(m)


def add_isochrone_layer(m, geojson_data, city_name):
    """Add isochrone polygon to the map."""
    folium.GeoJson(
        geojson_data,
        name=f'Isochrone {city_name}',
        style_function=lambda feature: {
            'fillColor': '#ff6600',
            'color': '#ff6600',
            'weight': 2,
            'fillOpacity': 0.2,
        },
        tooltip=f'1h dojezd od {city_name}'
    ).add_to(m)


def load_raster_as_tiles():
    """Convert GeoTIFF to web map tiles using leafmap/xyzservices approach."""
    # For now, we'll use a simpler approach with rasterio and folium's ImageOverlay
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    import numpy as np
    import io
    import base64
    from PIL import Image

    return None  # Will be implemented differently


def load_falchi_overlay():
    """Load pre-generated Falchi PNG overlay."""
    if FALCHI_PNG.exists():
        with open(FALCHI_PNG, 'rb') as f:
            png_bytes = f.read()
        png_base64 = base64.b64encode(png_bytes).decode('utf-8')
        return png_base64
    return None


def add_falchi_layer(m, opacity=0.5):
    """Add Falchi light pollution overlay to the map."""
    if not FALCHI_PNG.exists():
        print("  WARNING: Falchi overlay PNG not found!")
        return

    min_lon, min_lat, max_lon, max_lat = FALCHI_BOUNDS

    # Create image overlay using file path
    falchi_overlay = folium.raster_layers.ImageOverlay(
        image=str(FALCHI_PNG),
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=opacity,
        interactive=False,
        zindex=1
    )
    falchi_overlay.add_to(m)
    return falchi_overlay


def create_regional_map():
    """
    Create regional view map: user selects a region, sees isochrone + viewpoints.
    """
    print("Creating regional map...")

    # Load data
    best_sites = pd.read_csv(BEST_SITES_CSV)
    reachable = pd.read_csv(REACHABLE_CSV)

    # Create map centered on CZ
    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap')

    # Add title
    title_html = '''
    <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">Perseidy - Výběr kraje</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">Klikni na hvězdičku pro izochronu daného kraje</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Add isochrones as clickable layers
    isochrone_group = folium.FeatureGroup(name="Isochrony")

    for _, row in best_sites.iterrows():
        city = row['reachable_from_city']
        geojson_file = ISOCHRONES_DIR / f"isochrone_{city}.geojson"

        if not geojson_file.exists():
            continue

        with open(geojson_file) as f:
            geojson_data = json.load(f)

        # Create marker for the city
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=f"<b>{city}</b><br>Nejtemnější místo: {row['name']}<br>Tma: {row['darkness_value']:.4f}",
            icon=folium.Icon(color='red', icon='star', prefix='fa'),
            tooltip=f'{city} - 1h izochrona'
        ).add_to(isochrone_group)

        # Add isochrone polygon
        folium.GeoJson(
            geojson_data,
            name=f'Isochrone {city}',
            style_function=lambda feature, c=city: {
                'fillColor': '#ff6600',
                'color': '#ff6600',
                'weight': 2,
                'fillOpacity': 0.15,
            },
            highlight_function=lambda x: {'fillOpacity': 0.3}
        ).add_to(isochrone_group)

    isochrone_group.add_to(m)

    # Add Falchi light pollution overlay
    add_falchi_layer(m, opacity=0.5)

    # Add dark sites within this region (filtered by isochrone)
    dark_sites_group = folium.FeatureGroup(name="Tmavá místa (< 0.16)")

    for _, row in reachable.iterrows():
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val) or val >= 0.16:
            continue

        color = get_falchi_color(val)
        name = row.get('name', 'Unnamed POI')
        popup_text = f"<b>{name}</b><br>Tma: {val:.4f}<br>{get_falchi_category(val)}"

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=5,
            color='#333333',
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(dark_sites_group)

    dark_sites_group.add_to(m)

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    # Save
    output_file = OUTPUT_DIR / "perseidy_regional.html"
    m.save(output_file)
    print(f"  Saved: {output_file}")
    return output_file


def create_full_cz_map():
    """
    Create full CZ map: entire Czech Republic with Falchi background + all viewpoints.
    User manually explores to find their spot.
    """
    print("Creating full CZ map...")

    # Load viewpoints with darkness
    df = pd.read_csv(VIEWPOINTS_CSV)

    # Filter to reasonable bounds for CZ
    df = df[(df['lat'] >= 48.5) & (df['lat'] <= 51.2)]
    df = df[(df['lon'] >= 12) & (df['lon'] <= 19)]

    # Create map
    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap')

    # Title
    title_html = '''
    <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">Perseidy - Celá ČR</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">Prozkoumej mapu a najdi svoje místo</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Legend
    legend_html = '''
    <div style="position: fixed; bottom: 30px; right: 10px; z-index: 1000;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3); font-size: 11px;">
        <b>Světelné znečištění</b><br>
        <i style="background: #000000"></i> Přirozená tma<br>
        <i style="background: #00008B"></i> Slabé znečištění<br>
        <i style="background: #0000FF"></i> Mírné znečištění<br>
        <i style="background: #444AF8"></i> Střední znečištění<br>
        <i style="background: #006400"></i> Znečištěná<br>
        <i style="background: #FFFF00"></i> Silné znečištění<br>
        <i style="background: #FF0000"></i> Velmi silné<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add Falchi light pollution overlay
    add_falchi_layer(m, opacity=0.5)

    # Add all dark sites
    for _, row in df.iterrows():
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val):
            continue

        # Only show sites with darkness < 0.32 (reasonable for observation)
        if val >= 0.32:
            continue

        color = get_falchi_color(val)
        name = row.get('name', 'Unnamed POI')
        popup_text = f"<b>{name}</b><br>Tma: {val:.4f}<br>{get_falchi_category(val)}"

        # Size based on darkness (darker = larger)
        radius = max(3, min(8, 10 - val * 30))

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius,
            color='#222222',
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

    m.save(OUTPUT_DIR / "perseidy_full_cz.html")
    print(f"  Saved: {OUTPUT_DIR / 'perseidy_full_cz.html'}")
    return OUTPUT_DIR / "perseidy_full_cz.html"


def create_top_sites_map():
    """
    Create top sites map: table of darkest sites per city with markers.
    """
    print("Creating top sites map...")

    best_sites = pd.read_csv(BEST_SITES_CSV)

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap')

    # Title
    title_html = '''
    <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">Perseidy - Nejtemnější místa per kraj</h3>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Add Falchi light pollution overlay
    add_falchi_layer(m, opacity=0.5)

    # Add markers for best sites
    for _, row in best_sites.iterrows():
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val):
            continue

        color = get_falchi_color(val)
        name = row.get('name', 'Unnamed POI')
        city = row['reachable_from_city']
        popup_text = f"""
        <b>{city}</b><br>
        <b>{name}</b><br>
        Tma: {val:.4f}<br>
        {get_falchi_category(val)}<br>
        <i>Lat/Lon: {row['lat']:.4f}, {row['lon']:.4f}</i>
        """

        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_text, max_width=350),
            icon=folium.Icon(color='red', icon='star', prefix='fa'),
            tooltip=f'{city}: {name}'
        ).add_to(m)

    m.save(OUTPUT_DIR / "perseidy_top_sites.html")
    print(f"  Saved: {OUTPUT_DIR / 'perseidy_top_sites.html'}")
    return OUTPUT_DIR / "perseidy_top_sites.html"


def main():
    print("=" * 60)
    print("Generating HTML maps for Perseidy project")
    print("=" * 60)

    OUTPUT_DIR.mkdir(exist_ok=True)

    create_regional_map()
    create_full_cz_map()
    create_top_sites_map()

    print("\n" + "=" * 60)
    print("All maps generated!")
    print("Output files:")
    print("  - output/perseidy_regional.html")
    print("  - output/perseidy_full_cz.html")
    print("  - output/perseidy_top_sites.html")


if __name__ == "__main__":
    main()
