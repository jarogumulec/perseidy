# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Create interactive HTML maps for Perseids project.
Simple version with long checkbox list - no JavaScript complexity.
"""

import pandas as pd
import json
from pathlib import Path
import folium
from publish_html import save_html_for_pages, nav_links_html, ratio_legend_html

# Paths
OUTPUT_DIR = Path(__file__).parent / "output"
ISOCHRONES_DIR = Path(__file__).parent / "isochrones"

FALCHI_PNG = OUTPUT_DIR / "falchi_overlay.png"
FALCHI_BOUNDS_JSON = OUTPUT_DIR / "falchi_bounds.json"

# Astronomy strict inputs (active)
VIEWPOINTS_CSV = OUTPUT_DIR / "viewpoints_with_darkness_astronomystrict.csv"
BEST_SITES_CSV = OUTPUT_DIR / "best_sites_per_city_astronomystrict.csv"
REACHABLE_CSV = OUTPUT_DIR / "reachable_dark_sites_astronomystrict.csv"

# Original clean inputs kept here for quick manual rollback:
# VIEWPOINTS_CSV = OUTPUT_DIR / "viewpoints_with_darkness.csv"
# BEST_SITES_CSV = OUTPUT_DIR / "best_sites_per_city.csv"
# REACHABLE_CSV = OUTPUT_DIR / "reachable_dark_sites.csv"

REGIONAL_MAP_HTML = OUTPUT_DIR / "perseidy_regional.html"
FULL_CZ_MAP_HTML = OUTPUT_DIR / "perseidy_full_cz.html"

# Optional alternative names if you ever want separate strict HTML files:
# REGIONAL_MAP_HTML = OUTPUT_DIR / "perseidy_regional_astronomystrict.html"
# FULL_CZ_MAP_HTML = OUTPUT_DIR / "perseidy_full_cz_astronomystrict.html"

# Falchi data
FALCHI_DATA = [
    (0.01, "<1.74", "#000000", "Přirozená tma"),
    (0.02, "1.74–3.48", "#808080", "Velmi tmavá"),
    (0.04, "3.48–6.96", "#A9A9A9", "Téměř přirozená"),
    (0.08, "6.96–13.9", "#00008B", "Slabé znečištění"),
    (0.16, "13.9–27.8", "#0000FF", "Mírné znečištění"),
    (0.32, "27.8–55.7", "#444AF8", "Střední znečištění"),
    (0.64, "55.7–111", "#006400", "Znečištěná"),
    (1.28, "111–223", "#008000", "Silné znečištění"),
    (2.56, "223–445", "#FFFF00", "Velmi silné znečištění"),
    (5.12, "445–890", "#FFA500", "Extrémní znečištění"),
    (10.24, "890–1780", "#FF0000", "Oběžná zóna"),
    (float('inf'), ">1780", "#FFFFFF", "Totální znečištění"),
]

CITY_TO_REGION = {
    "Praha": ("Hlavní město Praha", [49.8, 15.5]),
    "Příbram": ("Středočeský kraj", [49.7, 14.1]),
    "České Budějovice": ("Jihočeský kraj", [49.0, 14.5]),
    "Plzeň": ("Plzeňský kraj", [49.7, 13.4]),
    "Karlovy Vary": ("Karlovarský kraj", [50.2, 12.9]),
    "Ústí nad Labem": ("Ústecký kraj", [50.7, 14.0]),
    "Liberec": ("Liberecký kraj", [50.8, 15.1]),
    "Hradec Králové": ("Královéhradecký kraj", [50.2, 15.8]),
    "Pardubice": ("Pardubický kraj", [50.0, 15.8]),
    "Jihlava": ("Kraj Vysočina", [49.4, 15.6]),
    "Brno": ("Jihomoravský kraj", [49.2, 16.6]),
    "Olomouc": ("Olomoucký kraj", [49.6, 17.3]),
    "Zlín": ("Zlínský kraj", [49.2, 17.7]),
    "Ostrava": ("Moravskoslezský kraj", [49.8, 18.3]),
}


def get_falchi_color(value):
    if pd.isna(value):
        return '#888888'
    for threshold, _, color, _ in FALCHI_DATA:
        if value <= threshold:
            return color
    return '#FFFFFF'


def get_falchi_category(value):
    if pd.isna(value):
        return "Neznámá"
    for threshold, _, _, label in FALCHI_DATA:
        if value <= threshold:
            return label
    return "Totální znečištění"


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


def create_regional_map(reachable_csv: Path, best_sites_csv: Path):
    print("Creating regional map...")

    reachable = pd.read_csv(reachable_csv)
    best_sites = pd.read_csv(best_sites_csv)

    # Create set of top site coordinates for highlighting
    top_site_coords = set()
    for _, row in best_sites.iterrows():
        top_site_coords.add((round(row['lat'], 4), round(row['lon'], 4)))

    # Create map with dark tiles
    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='cartodb.dark_matter', control_scale=True)

    # Add Falchi first (bottom layer)
    add_falchi_layer(m)

    # Process each city in the manual order defined in CITY_TO_REGION.
    # Prague is shown first by default.
    for city, (region_label, center) in CITY_TO_REGION.items():
        geojson_file = ISOCHRONES_DIR / "isochrone_{}.geojson".format(city)
        if not geojson_file.exists():
            continue

        with open(geojson_file) as f:
            iso_data = json.load(f)

        region_sites = reachable[reachable['reachable_from_city'] == city]
        region_sites = region_sites[region_sites['darkness_value'] < 0.16]

        show_default = (city == "Praha")

        # Create ONE FeatureGroup containing both isochrone and points
        region_group = folium.FeatureGroup(
            name=u'{}: Izochrona + Body'.format(region_label),
            show=show_default,
        )

        # Add isochrone to group (below points)
        iso_layer = folium.GeoJson(
            iso_data,
            style_function=lambda x: {'fillColor': '#ff6600', 'color': '#ff6600', 'weight': 2, 'fillOpacity': 0.2}
        )
        iso_layer.add_to(region_group)

        # Add points to group (on top, clickable)
        for _, row in region_sites.iterrows():
            val = row.get('darkness_value', None)
            if val is None or pd.isna(val):
                continue
            color = get_falchi_color(val)
            name = row.get('name', 'Unnamed POI')
            popup_text = u"<b>{}</b><br>Tma: {:.4f}<br>{}".format(name, val, get_falchi_category(val))

            # Check if this is a top site (best in its region)
            point_coord = (round(row['lat'], 4), round(row['lon'], 4))
            is_top = point_coord in top_site_coords

            # Top sites have red border for emphasis
            if is_top:
                circle = folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=7,
                    color='#FF0000',  # Red border
                    weight=2,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.85,
                    popup=folium.Popup(popup_text + "<br><b>★ Nejtemnější v kraji</b>", max_width=300),
                    tooltip=u"★ {}".format(name) if is_top else name
                )
            else:
                circle = folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=5,
                    color='#222222',
                    weight=1.5,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.85,
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=name
                )
            circle.add_to(region_group)

        # Add entire group to map
        region_group.add_to(m)

    # Compact corner navigation and ratio-only legend.
    m.get_root().html.add_child(
        folium.Element(nav_links_html([
            ("GitHub", "https://github.com/jarogumulec/perseidy"),
            ("Celá ČR", "perseidy_full_cz.html"),
            ("Brno", "perseidy_brno.html"),
            ("Kopřivnice", "perseidy_koprivnice.html"),
        ]))
    )
    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    m.get_root().html.add_child(folium.Element(ratio_legend_html()))

    output_file = REGIONAL_MAP_HTML
    saved_file, docs_file = save_html_for_pages(m, output_file)
    print("  Saved: {}".format(saved_file))
    print("  Mirrored to: {}".format(docs_file))
    return output_file


def create_full_cz_map(viewpoints_csv: Path):
    print("Creating full CZ map...")

    df = pd.read_csv(viewpoints_csv)
    df = df[(df['lat'] >= 48.5) & (df['lat'] <= 51.2)]
    df = df[(df['lon'] >= 12) & (df['lon'] <= 19)]

    darkest_site = df[df['darkness_value'].notna()].sort_values('darkness_value').iloc[0]

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='cartodb.dark_matter', control_scale=True)

    # Add Falchi
    add_falchi_layer(m)

    # Add all points
    for _, row in df.iterrows():
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val) or val >= 0.32:
            continue

        color = get_falchi_color(val)
        name = row.get('name', 'Unnamed POI')
        popup_text = u"<b>{}</b><br>Tma: {:.4f}<br>{}".format(name, val, get_falchi_category(val))
        radius = max(3, min(8, 10 - val * 30))

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius, color='#222222', weight=1.5,
            fill=True, fill_color=color, fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

    # Darkest site marker
    darkest_popup = u"""
    <b>NEJTEMNĚJŠÍ MÍSTO V ČR</b><br>
    <b>{}</b><br>
    Tma: {:.4f}<br>
    Lat/Lon: {:.4f}, {:.4f}
    """.format(darkest_site.get('name', '?'), darkest_site['darkness_value'],
               darkest_site['lat'], darkest_site['lon'])

    folium.Marker(
        location=[darkest_site['lat'], darkest_site['lon']],
        popup=folium.Popup(darkest_popup, max_width=300),
        icon=folium.Icon(color='green', icon='star', prefix='fa'),
        tooltip='Nejtemnější místo v ČR'
    ).add_to(m)

    # Legend with physical units
    m.get_root().html.add_child(
        folium.Element(nav_links_html([
            ("GitHub", "https://github.com/jarogumulec/perseidy"),
            ("Regional", "perseidy_regional.html"),
        ]))
    )
    m.get_root().html.add_child(folium.Element(ratio_legend_html()))

    output_file = FULL_CZ_MAP_HTML
    saved_file, docs_file = save_html_for_pages(m, output_file)
    print("  Saved: {}".format(saved_file))
    print("  Mirrored to: {}".format(docs_file))
    return output_file


def main():
    viewpoints_csv = VIEWPOINTS_CSV
    reachable_csv = REACHABLE_CSV
    best_sites_csv = BEST_SITES_CSV

    print("=" * 60)
    print("Generating HTML maps for Perseidy project")
    print("=" * 60)
    print(f"Input viewpoints CSV: {viewpoints_csv}")
    print(f"Input reachable CSV: {reachable_csv}")
    print(f"Input best sites CSV: {best_sites_csv}")
    print(f"Output regional map: {REGIONAL_MAP_HTML}")
    print(f"Output full CZ map: {FULL_CZ_MAP_HTML}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    create_regional_map(reachable_csv=reachable_csv, best_sites_csv=best_sites_csv)
    create_full_cz_map(viewpoints_csv=viewpoints_csv)

    print("\n" + "=" * 60)
    print("All maps generated! (2 HTML files)")


if __name__ == "__main__":
    main()
