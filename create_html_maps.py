#!/usr/bin/env python3
"""
Create interactive HTML maps for Perseids project.
"""

import pandas as pd
import json
from pathlib import Path
import folium

# Paths
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
ISOCHRONES_DIR = Path(__file__).parent / "isochrones"

FALCHI_PNG = OUTPUT_DIR / "falchi_overlay.png"
FALCHI_BOUNDS_JSON = OUTPUT_DIR / "falchi_bounds.json"
VIEWPOINTS_CSV = OUTPUT_DIR / "viewpoints_with_darkness.csv"
BEST_SITES_CSV = OUTPUT_DIR / "best_sites_per_city.csv"
REACHABLE_CSV = OUTPUT_DIR / "reachable_dark_sites.csv"

# Falchi data with absolute values (from Falchi et al. 2016, Table 1)
# Ratio | Artificial brightness (μcd/m²) | Approx total brightness (mcd/m²) | Color
FALCHI_DATA = [
    (0.01, "<1.74", "<0.176", "#000000", "Přirozená tma"),
    (0.02, "1.74–3.48", "0.176–0.177", "#808080", "Velmi tmavá"),
    (0.04, "3.48–6.96", "0.177–0.181", "#A9A9A9", "Téměř přirozená"),
    (0.08, "6.96–13.9", "0.181–0.188", "#00008B", "Slabé znečištění"),
    (0.16, "13.9–27.8", "0.188–0.202", "#0000FF", "Mírné znečištění"),
    (0.32, "27.8–55.7", "0.202–0.230", "#444AF8", "Střední znečištění"),
    (0.64, "55.7–111", "0.230–0.285", "#006400", "Znečištěná"),
    (1.28, "111–223", "0.285–0.397", "#008000", "Silné znečištění"),
    (2.56, "223–445", "0.397–0.619", "#FFFF00", "Velmi silné znečištění"),
    (5.12, "445–890", "0.619–1.065", "#FFA500", "Extrémní znečištění"),
    (10.24, "890–1780", "1.07–1.96", "#FF0000", "Oběžná zóna"),
    (20.48, "1780–3560", "1.96–3.74", "#FF00FF", "Totální světlo"),
    (40.96, "3560–7130", "3.74–7.30", "#FFC0CB", "Bez oblohy"),
    (float('inf'), ">7130", ">7.30", "#FFFFFF", "Totální znečištění"),
]

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
    if pd.isna(value):
        return '#888888'
    for threshold, _, _, color, _ in FALCHI_DATA:
        if value <= threshold:
            return color
    return '#FFFFFF'


def get_falchi_category(value):
    if pd.isna(value):
        return "Neznámá"
    for threshold, _, _, _, label in FALCHI_DATA:
        if value <= threshold:
            return label
    return "Totální znečištění"


def load_falchi_bounds():
    if FALCHI_BOUNDS_JSON.exists():
        with open(FALCHI_BOUNDS_JSON) as f:
            return json.load(f)
    return None


def add_falchi_layer(m):
    if not FALCHI_PNG.exists() or not FALCHI_BOUNDS_JSON.exists():
        return None

    with open(FALCHI_BOUNDS_JSON) as f:
        bounds_info = json.load(f)

    min_lat, min_lon = bounds_info['min_lat'], bounds_info['min_lon']
    max_lat, max_lon = bounds_info['max_lat'], bounds_info['max_lon']

    falchi_overlay = folium.raster_layers.ImageOverlay(
        image=str(FALCHI_PNG),
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=0.5,
        name="Světelné znečištění (Falchi 2015)"
    )
    falchi_overlay.add_to(m)
    return falchi_overlay


def create_legend_html():
    """Create legend HTML with full Falchi table."""
    rows = ""
    for threshold, art_bright, total_bright, color, label in FALCHI_DATA:
        if threshold == float('inf'):
            ratio_str = ">41"
        else:
            prev = [t for t, _, _, _, _ in FALCHI_DATA if t < threshold][-1] if threshold > 0.01 else 0
            if prev == 0:
                ratio_str = f"≤{threshold}"
            else:
                ratio_str = f"{prev*100:.0f}–{threshold*100:.0f} %"
        rows += f'''
        <tr><td style="background:{color};width:20px;height:15px;"></td>
            <td>{ratio_str}</td>
            <td>{art_bright}</td>
            <td>{total_bright}</td>
            <td>{label}</td></tr>'''

    return f'''
    <div style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3); font-size: 10px;
                max-height: 350px; overflow-y: auto;">
        <b>Světelné znečištění (Falchi et al. 2015)</b><br>
        <table style="border-collapse: collapse;">
            <tr><th></th><th>Ratio</th><th>Artif.<br>(μcd/m²)</th><th>Total<br>(mcd/m²)</th><th></th></tr>
            {rows}
        </table>
    </div>
    '''


def create_statistics_table_html(stats_df, title="Statistiky podle krajů"):
    """Create HTML table with statistics."""
    rows = ""
    for _, row in stats_df.iterrows():
        city = row['reachable_from_city']
        count = row.get('count', 0)
        min_d = f"{row['min_darkness']:.4f}" if pd.notna(row.get('min_darkness')) else "N/A"
        mean_d = f"{row['mean_darkness']:.4f}" if pd.notna(row.get('mean_darkness')) else "N/A"
        max_d = f"{row['max_darkness']:.4f}" if pd.notna(row.get('max_darkness')) else "N/A"
        rows += f'''
        <tr>
            <td>{city}</td>
            <td>{count}</td>
            <td>{min_d}</td>
            <td>{mean_d}</td>
            <td>{max_d}</td>
        </tr>'''

    return f'''
    <div style="position: fixed; bottom: 10px; left: 10px; z-index: 999;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3); font-size: 11px;
                max-height: 300px; overflow-y: auto; max-width: 400px;">
        <h4 style="margin: 0 0 10px 0;">{title}</h4>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><th>Kraj</th><th>Bodů</th><th>Min</th><th>Průměr</th><th>Max</th></tr>
            {rows}
        </table>
    </div>
    '''


def create_regional_map():
    print("Creating regional map...")

    best_sites = pd.read_csv(BEST_SITES_CSV)
    reachable = pd.read_csv(REACHABLE_CSV)

    # Default to first region: Praha
    DEFAULT_REGION = "Praha"

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap')

    # Title and dropdown
    dropdown_html = '''
    <div style="position: fixed; top: 10px; left: 10px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0 0 10px 0; font-size: 16px;">Perseidy - Výběr kraje</h3>
        <p style="margin: 0 0 10px 0; font-size: 11px;">Body jsou místa s dojezdem <1h z krajského města</p>
        <select id="region-select" onchange="filterByRegion(this.value)"
                style="padding: 8px; font-size: 14px;">
            <option value="">-- Vyber kraj --</option>
            '''
    for region_label, city in CZECH_REGIONS:
        selected = "selected" if city == DEFAULT_REGION else ""
        dropdown_html += f'<option value="{city}" {selected}>{region_label}</option>'
    dropdown_html += '</select></div>'

    m.get_root().html.add_child(folium.Element(dropdown_html))

    # Add Falchi overlay
    add_falchi_layer(m)

    # Group points by region and create layers
    region_groups = {}
    for city in [r[1] for r in CZECH_REGIONS]:
        geojson_file = ISOCHRONES_DIR / f"isochrone_{city}.geojson"
        if not geojson_file.exists():
            continue

        with open(geojson_file) as f:
            geojson_data = json.load(f)

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
                "geometry": {"type": "Point", "coordinates": [row['lon'], row['lat']]},
                "properties": {"popup": popup_text, "color": color}
            })

        if features:
            # Isochrone layer
            isochrone_layer = folium.GeoJson(
                geojson_data,
                name=f'Isochrone: {city}',
                style_function=lambda x: {'fillColor': '#ff6600', 'color': '#ff6600', 'weight': 2, 'fillOpacity': 0.2},
                show=False
            )
            isochrone_layer.add_to(m)

            # Points layer
            point_layer = folium.GeoJson(
                {"type": "FeatureCollection", "features": features},
                name=f'Body: {city}',
                style_function=lambda feature: {
                    'color': '#333333', 'weight': 1.5,
                    'fillColor': feature['properties']['color'],
                    'fillOpacity': 0.85
                },
                tooltip=folium.GeoJsonTooltip(fields=['popup'], aliases=['']),
                show=False
            )
            point_layer.add_to(m)

            region_groups[city] = {'isochrone': isochrone_layer, 'points': point_layer}

    # Show default region
    if DEFAULT_REGION in region_groups:
        region_groups[DEFAULT_REGION]['isochrone'].add_to(m)
        region_groups[DEFAULT_REGION]['points'].add_to(m)

    # JavaScript for switching regions
    js_code = '''
    <script>
    var currentLayers = [];
    function filterByRegion(city) {
        // Remove all existing layers
        currentLayers.forEach(function(layer) { map.removeLayer(layer); });
        currentLayers = [];

        if (!city) return;

        // Add isochrone and points for selected region
        if (window["iso_" + city]) {
            window["iso_" + city].addTo(map);
            currentLayers.push(window["iso_" + city]);
        }
        if (window["pts_" + city]) {
            window["pts_" + city].addTo(map);
            currentLayers.push(window["pts_" + city]);
        }
    }
    // Initialize with default
    filterByRegion("''' + DEFAULT_REGION + '''");
    </script>
    '''
    m.get_root().header.add_child(folium.Element(js_code))

    # Store layers in window for JS
    for city, layers in region_groups.items():
        m.get_root().header.add_child(folium.Element(
            f'<script>window["iso_{city}"] = "{layers["isochrone"].get_name()}";</script>'
        ))
        m.get_root().header.add_child(folium.Element(
            f'<script>window["pts_{city}"] = "{layers["points"].get_name()}";</script>'
        ))

    # Add legend
    m.get_root().html.add_child(folium.Element(create_legend_html()))

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    output_file = OUTPUT_DIR / "perseidy_regional.html"
    m.save(output_file)
    print(f"  Saved: {output_file}")
    return output_file


def create_full_cz_map():
    print("Creating full CZ map...")

    df = pd.read_csv(VIEWPOINTS_CSV)
    df = df[(df['lat'] >= 48.5) & (df['lat'] <= 51.2)]
    df = df[(df['lon'] >= 12) & (df['lon'] <= 19)]

    darkest_site = df[df['darkness_value'].notna()].sort_values('darkness_value').iloc[0]

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap')

    title_html = '''
    <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">Perseidy - Celá ČR</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">Prozkoumej mapu a najdi svoje místo</p>
        <p style="margin: 5px 0 0 0; font-size: 10px; color: #666;">ⓘ Data Falchi z 2015 mohou být místy zastaralá</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    add_falchi_layer(m)

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
            radius=radius, color='#222222', weight=1.5,
            fill=True, fill_color=color, fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(dark_sites_group)

    dark_sites_group.add_to(m)

    # Darkest site marker
    darkest_popup = f"""
    <b>NEJTEMNĚJŠÍ MÍSTO V ČR</b><br>
    <b>{darkest_site.get('name', 'Unnamed POI')}</b><br>
    Tma: {darkest_site['darkness_value']:.4f}<br>
    {get_falchi_category(darkest_site['darkness_value'])}<br>
    <i>Lat/Lon: {darkest_site['lat']:.4f}, {darkest_site['lon']:.4f}</i>
    """

    folium.Marker(
        location=[darkest_site['lat'], darkest_site['lon']],
        popup=folium.Popup(darkest_popup, max_width=350),
        icon=folium.Icon(color='green', icon='star', prefix='fa'),
        tooltip='Nejtemnější místo v ČR'
    ).add_to(m)

    m.get_root().html.add_child(folium.Element(create_legend_html()))
    folium.LayerControl(collapsed=False).add_to(m)

    output_file = OUTPUT_DIR / "perseidy_full_cz.html"
    m.save(output_file)
    print(f"  Saved: {output_file}")
    return output_file


def create_top_sites_map():
    print("Creating top sites map...")

    best_sites = pd.read_csv(BEST_SITES_CSV)

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='OpenStreetMap')

    title_html = '''
    <div style="position: fixed; top: 10px; left: 50px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">Perseidy - Nejtemnější místa per kraj</h3>
        <p style="margin: 5px 0 0 0; font-size: 11px;">Ukazováno je nejlepší místo v rámci 1h izochrony z krajského města</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    add_falchi_layer(m)

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

    # Add statistics table
    stats_df = pd.read_csv(REACHABLE_CSV).groupby('reachable_from_city').agg({
        'darkness_value': ['count', 'min', 'mean', 'max']
    }).reset_index()
    stats_df.columns = ['reachable_from_city', 'count', 'min_darkness', 'mean_darkness', 'max_darkness']

    m.get_root().html.add_child(folium.Element(create_statistics_table_html(stats_df)))
    m.get_root().html.add_child(folium.Element(create_legend_html()))
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


if __name__ == "__main__":
    main()
