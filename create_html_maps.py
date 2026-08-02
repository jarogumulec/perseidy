#!/usr/bin/env python3
"""
Create interactive HTML maps for Perseids project.

Generates 3 map variants:
1. Regional view: Select a region via dropdown, shows only viewpoints in that region
2. Full CZ view: Entire Czech Republic with all viewpoints + darkest site highlighted
3. Top sites: Darkest sites per city with markers
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
FALCHI_BOUNDS_JSON = OUTPUT_DIR / "falchi_bounds.json"
VIEWPOINTS_CSV = OUTPUT_DIR / "viewpoints_with_darkness.csv"
BEST_SITES_CSV = OUTPUT_DIR / "best_sites_per_city.csv"
REACHABLE_CSV = OUTPUT_DIR / "reachable_dark_sites.csv"

# Falchi color palette (matches QGIS export)
FALCHI_COLORS = [
    (0.01, '#000000'),  # <= 0.01  - Černá
    (0.02, '#808080'),  # 0.01-0.02 - Tmavě šedá
    (0.04, '#A9A9A9'),  # 0.02-0.04 - Šedá
    (0.08, '#00008B'),  # 0.04-0.08 - Tmavě modrá
    (0.16, '#0000FF'),  # 0.08-0.16 - Modrá
    (0.32, '#444AF8'),  # 0.16-0.32 - Světle modrá
    (0.64, '#006400'),  # 0.32-0.64 - Tmavě zelená
    (1.28, '#008000'),  # 0.64-1.28 - Zelená
    (2.56, '#FFFF00'),  # 1.28-2.56 - Žlutá
    (5.12, '#FFA500'),  # 2.56-5.12 - Oranžová
    (10.24, '#FF0000'),  # 5.12-10.24 - Červená
    (20.48, '#FF00FF'),  # 10.24-20.48 - Purpurová
    (40.96, '#FFC0CB'),  # 20.48-40.96 - Růžová
]

FALCHI_LABELS = {
    0.01: "Přirozená tma",
    0.02: "Velmi tmavá",
    0.04: "Téměř přirozená",
    0.08: "Slabé znečištění",
    0.16: "Mírné znečištění",
    0.32: "Střední znečištění",
    0.64: "Znečištěná",
    1.28: "Silné znečištění",
    2.56: "Velmi silné znečištění",
    5.12: "Extrémní znečištění",
    10.24: "Oběžná zóna",
    20.48: "Totální světlo",
    40.96: "Bez oblohy",
}

# Czech regions
CZECH_REGIONS = [
    ("Hlavní město Praha", "Praha"),
    ("Středočeský kraj", "Příbram"),
    ("Jihočeský kraj", "České Budějovice"),
    ("Plzeňský kraj", "Plzeň"),
    ("Karlovarský kraj", "Karlovy Vary"),
    ("Ústecký kraj", "Ústí nad Labem"),
    ("Liberecký kraj", "Liberec"),
    ("Královéhradecký kraj", "Hradec Králové"),
    ("Pardubický kraj", "Pardubice"),
    ("Kraj Vysočina", "Jihlava"),
    ("Jihomoravský kraj", "Brno"),
    ("Olomoucký kraj", "Olomouc"),
    ("Zlínský kraj", "Zlín"),
    ("Moravskoslezský kraj", "Ostrava"),
]


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
    for threshold, label in sorted(FALCHI_LABELS.items()):
        if value <= threshold:
            return label
    return "Bez oblohy"


def load_falchi_bounds():
    """Load Falchi bounds from JSON file."""
    if FALCHI_BOUNDS_JSON.exists():
        with open(FALCHI_BOUNDS_JSON) as f:
            return json.load(f)
    return None


def add_falchi_layer(m):
    """Add Falchi light pollution overlay to the map."""
    if not FALCHI_PNG.exists() or not FALCHI_BOUNDS_JSON.exists():
        print("  WARNING: Falchi overlay files not found!")
        return None

    with open(FALCHI_BOUNDS_JSON) as f:
        bounds_info = json.load(f)

    min_lat, min_lon = bounds_info['min_lat'], bounds_info['min_lon']
    max_lat, max_lon = bounds_info['max_lat'], bounds_info['max_lon']

    falchi_overlay = folium.raster_layers.ImageOverlay(
        image=str(FALCHI_PNG),
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=0.5,
        interactive=False,
        name="Světelné znečištění (Falchi)"
    )
    falchi_overlay.add_to(m)
    return falchi_overlay


def add_legend(m):
    """Add legend for Falchi light pollution levels."""
    legend_html = '''
    <div style="position: fixed; bottom: 30px; right: 10px; z-index: 1000;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3); font-size: 11px;
                max-height: 300px; overflow-y: auto;">
        <b>Světelné znečištění</b><br>
        <i style="background: #000000; width: 15px; height: 15px; display: inline-block;"></i> Přirozená tma<br>
        <i style="background: #808080; width: 15px; height: 15px; display: inline-block;"></i> Velmi tmavá<br>
        <i style="background: #A9A9A9; width: 15px; height: 15px; display: inline-block;"></i> Téměř přirozená<br>
        <i style="background: #00008B; width: 15px; height: 15px; display: inline-block;"></i> Slabé znečištění<br>
        <i style="background: #0000FF; width: 15px; height: 15px; display: inline-block;"></i> Mírné znečištění<br>
        <i style="background: #444AF8; width: 15px; height: 15px; display: inline-block;"></i> Střední znečištění<br>
        <i style="background: #006400; width: 15px; height: 15px; display: inline-block;"></i> Znečištěná<br>
        <i style="background: #008000; width: 15px; height: 15px; display: inline-block;"></i> Silné znečištění<br>
        <i style="background: #FFFF00; width: 15px; height: 15px; display: inline-block;"></i> Velmi silné<br>
        <i style="background: #FFA500; width: 15px; height: 15px; display: inline-block;"></i> Extrémní<br>
        <i style="background: #FF0000; width: 15px; height: 15px; display: inline-block;"></i> Oběžná zóna<br>
        <i style="background: #FF00FF; width: 15px; height: 15px; display: inline-block;"></i> Totální světlo<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))


def create_regional_map():
    """
    Create regional view map: user selects a region from dropdown,
    sees only viewpoints within that region's isochrone.
    """
    print("Creating regional map...")

    best_sites = pd.read_csv(BEST_SITES_CSV)
    reachable = pd.read_csv(REACHABLE_CSV)

    # Create map centered on CZ
    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap')

    # Title and dropdown
    dropdown_html = '''
    <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0 0 10px 0;">Perseidy - Výběr kraje</h3>
        <select id="region-select" onchange="filterByRegion(this.value)"
                style="padding: 8px; font-size: 14px;">
            <option value="">-- Vyber kraj --</option>
            '''
    for region_label, city in CZECH_REGIONS:
        dropdown_html += f'<option value="{city}">{region_label}</option>'
    dropdown_html += '''
        </select>
    </div>

    <script>
    var currentLayer = null;
    function filterByRegion(region) {
        if (currentLayer) {
            map.removeLayer(currentLayer);
        }
        if (!region) {
            return;
        }
        // This will be populated by Folium layers
        var layerName = 'region_' + region;
        if (window[layerName]) {
            currentLayer = window[layerName];
            currentLayer.addTo(map);
            // Zoom to bounds
            var group = new L.featureGroup(window[layerName].getLayers());
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }
    </script>
    '''
    m.get_root().html.add_child(folium.Element(dropdown_html))

    # Add Falchi overlay
    add_falchi_layer(m)

    # Group points by region
    region_groups = {}
    for city in [r[1] for r in CZECH_REGIONS]:
        geojson_file = ISOCHRONES_DIR / f"isochrone_{city}.geojson"
        if not geojson_file.exists():
            continue

        with open(geojson_file) as f:
            geojson_data = json.load(f)

        # Get isochrone bounds for zooming
        coords = geojson_data['features'][0]['geometry']['coordinates'][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        # Filter reachable sites for this region
        region_sites = reachable[reachable['reachable_from_city'] == city]
        region_sites = region_sites[region_sites['darkness_value'] < 0.16]

        # Create GeoJSON for points in this region
        features = []
        for _, row in region_sites.iterrows():
            val = row.get('darkness_value', None)
            if val is None or pd.isna(val):
                continue
            color = get_falchi_color(val)
            name = row.get('name', 'Unnamed POI')
            popup_text = f"<b>{name}</b><br>Tma: {val:.4f}<br>{get_falchi_category(val)}"

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['lon'], row['lat']]
                },
                "properties": {
                    "popup": popup_text,
                    "color": color
                }
            })

        if features:
            point_layer = folium.GeoJson(
                {"type": "FeatureCollection", "features": features},
                name=f'Region: {city}',
                style_function=lambda feature: {
                    'color': '#333333',
                    'weight': 1.5,
                    'fillColor': feature['properties']['color'],
                    'fillOpacity': 0.85
                },
                tooltip=folium.GeoJsonTooltip(fields=['popup'], aliases=[''])
            )
            point_layer.add_to(m)

            # Store in window for JavaScript access
            layer_id = f'region_{city}'
            m.get_root().header.add_child(folium.Element(
                f'<script>window["{layer_id}"] = {point_layer.get_name()};</script>'
            ))

    # Add legend
    add_legend(m)

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    output_file = OUTPUT_DIR / "perseidy_regional.html"
    m.save(output_file)
    print(f"  Saved: {output_file}")
    return output_file


def create_full_cz_map():
    """
    Create full CZ map: entire Czech Republic with all viewpoints.
    Highlights the darkest site in CZ.
    """
    print("Creating full CZ map...")

    df = pd.read_csv(VIEWPOINTS_CSV)

    # Filter to CZ bounds
    df = df[(df['lat'] >= 48.5) & (df['lat'] <= 51.2)]
    df = df[(df['lon'] >= 12) & (df['lon'] <= 19)]

    # Find darkest site
    darkest_site = df[df['darkness_value'].notna()].sort_values('darkness_value').iloc[0]

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

    # Add Falchi overlay
    add_falchi_layer(m)

    # Group for layer control
    dark_sites_group = folium.FeatureGroup(name="Výhledová místa (< 0.32)")

    for _, row in df.iterrows():
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val) or val >= 0.32:
            continue

        color = get_falchi_color(val)
        name = row.get('name', 'Unnamed POI')
        popup_text = f"<b>{name}</b><br>Tma: {val:.4f}<br>{get_falchi_category(val)}"

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
        ).add_to(dark_sites_group)

    dark_sites_group.add_to(m)

    # Highlight darkest site
    darkest_name = darkest_site.get('name', 'Unnamed POI')
    darkest_val = darkest_site['darkness_value']
    darkest_popup = f"""
    <b>NEJTEMNĚJŠÍ MÍSTO V ČR</b><br>
    <b>{darkest_name}</b><br>
    Tma: {darkest_val:.4f}<br>
    {get_falchi_category(darkest_val)}<br>
    <i>Lat/Lon: {darkest_site['lat']:.4f}, {darkest_site['lon']:.4f}</i>
    """

    folium.Marker(
        location=[darkest_site['lat'], darkest_site['lon']],
        popup=folium.Popup(darkest_popup, max_width=350),
        icon=folium.Icon(color='green', icon='star', prefix='fa'),
        tooltip='Nejtemnější místo v ČR'
    ).add_to(m)

    # Add legend
    add_legend(m)

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    output_file = OUTPUT_DIR / "perseidy_full_cz.html"
    m.save(output_file)
    print(f"  Saved: {output_file}")
    return output_file


def create_top_sites_map():
    """
    Create top sites map: darkest sites per city with markers.
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

    # Add Falchi overlay
    add_falchi_layer(m)

    # Group for sites
    sites_group = folium.FeatureGroup(name="Nejtemnější místa per kraj")

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
        ).add_to(sites_group)

    sites_group.add_to(m)

    # Add legend
    add_legend(m)

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    output_file = OUTPUT_DIR / "perseidy_top_sites.html"
    m.save(output_file)
    print(f"  Saved: {output_file}")
    return output_file


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
