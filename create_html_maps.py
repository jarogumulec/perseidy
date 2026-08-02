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

# Paths
OUTPUT_DIR = Path(__file__).parent / "output"
ISOCHRONES_DIR = Path(__file__).parent / "isochrones"

FALCHI_PNG = OUTPUT_DIR / "falchi_overlay.png"
FALCHI_BOUNDS_JSON = OUTPUT_DIR / "falchi_bounds.json"
VIEWPOINTS_CSV = OUTPUT_DIR / "viewpoints_with_darkness.csv"
BEST_SITES_CSV = OUTPUT_DIR / "best_sites_per_city.csv"
REACHABLE_CSV = OUTPUT_DIR / "reachable_dark_sites.csv"

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


def create_regional_map():
    print("Creating regional map...")

    reachable = pd.read_csv(REACHABLE_CSV)

    # Create map with dark tiles
    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='cartodb.dark_matter')

    # Add Falchi first (bottom layer)
    add_falchi_layer(m)

    # Process each city - create ONE FeatureGroup with isochrone + points together
    # One checkbox controls both for each region
    for city, (region_label, center) in CITY_TO_REGION.items():
        geojson_file = ISOCHRONES_DIR / "isochrone_{}.geojson".format(city)
        if not geojson_file.exists():
            continue

        with open(geojson_file) as f:
            iso_data = json.load(f)

        # Get points for this region
        region_sites = reachable[reachable['reachable_from_city'] == city]
        region_sites = region_sites[region_sites['darkness_value'] < 0.16]

        # Only show Praha initially
        show_praha = (city == "Praha")

        # Create ONE FeatureGroup containing both isochrone and points
        region_group = folium.FeatureGroup(name=u'{}: Izochrona + Body'.format(region_label), show=show_praha)

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

            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=5,
                color='#222222',
                weight=1.5,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=name
            ).add_to(region_group)

        # Add entire group to map
        region_group.add_to(m)

    # Layer control on the right - shows all checkboxes
    folium.LayerControl(collapsed=False, position='topright').add_to(m)

    # Compact legend with physical units (from Falchi et al. 2016, Table 1)
    legend_html = u'''
    <div style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 5px rgba(0,0,0,0.3); font-size: 9px;">
        <b>Falchi 2015 - Světelné znečištění</b><br>
        <table>
            <tr><th></th><th>Ratio</th><th>Artif.<br>(μcd/m²)</th><th>Total<br>(mcd/m²)</th></tr>
            <tr><td style="background:#000000;width:12px;height:10px;"></td><td>≤1%</td><td>&lt;1.74</td><td>&lt;0.176</td></tr>
            <tr><td style="background:#808080;width:12px;height:10px;"></td><td>1-2%</td><td>1.74-3.48</td><td>0.176-0.177</td></tr>
            <tr><td style="background:#A9A9A9;width:12px;height:10px;"></td><td>2-4%</td><td>3.48-6.96</td><td>0.177-0.181</td></tr>
            <tr><td style="background:#00008B;width:12px;height:10px;"></td><td>4-8%</td><td>6.96-13.9</td><td>0.181-0.188</td></tr>
            <tr><td style="background:#0000FF;width:12px;height:10px;"></td><td>8-16%</td><td>13.9-27.8</td><td>0.188-0.202</td></tr>
            <tr><td style="background:#444AF8;width:12px;height:10px;"></td><td>16-32%</td><td>27.8-55.7</td><td>0.202-0.230</td></tr>
            <tr><td style="background:#006400;width:12px;height:10px;"></td><td>32-64%</td><td>55.7-111</td><td>0.230-0.285</td></tr>
            <tr><td style="background:#008000;width:12px;height:10px;"></td><td>64-128%</td><td>111-223</td><td>0.285-0.397</td></tr>
            <tr><td style="background:#FFFF00;width:12px;height:10px;"></td><td>>128%</td><td>&gt;223</td><td>&gt;0.397</td></tr>
        </table>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    output_file = OUTPUT_DIR / "perseidy_regional.html"
    m.save(output_file)
    print("  Saved: {}".format(output_file))
    return output_file


def create_full_cz_map():
    print("Creating full CZ map...")

    df = pd.read_csv(VIEWPOINTS_CSV)
    df = df[(df['lat'] >= 48.5) & (df['lat'] <= 51.2)]
    df = df[(df['lon'] >= 12) & (df['lon'] <= 19)]

    darkest_site = df[df['darkness_value'].notna()].sort_values('darkness_value').iloc[0]

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='cartodb.dark_matter')

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
    legend_html = u'''
    <div style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 5px rgba(0,0,0,0.3); font-size: 9px;">
        <b>Falchi 2015 - Světelné znečištění</b><br>
        <table>
            <tr><th></th><th>Ratio</th><th>Artif.<br>(μcd/m²)</th><th>Total<br>(mcd/m²)</th></tr>
            <tr><td style="background:#000000;width:12px;height:10px;"></td><td>≤1%</td><td>&lt;1.74</td><td>&lt;0.176</td></tr>
            <tr><td style="background:#808080;width:12px;height:10px;"></td><td>1-2%</td><td>1.74-3.48</td><td>0.176-0.177</td></tr>
            <tr><td style="background:#A9A9A9;width:12px;height:10px;"></td><td>2-4%</td><td>3.48-6.96</td><td>0.177-0.181</td></tr>
            <tr><td style="background:#00008B;width:12px;height:10px;"></td><td>4-8%</td><td>6.96-13.9</td><td>0.181-0.188</td></tr>
            <tr><td style="background:#0000FF;width:12px;height:10px;"></td><td>8-16%</td><td>13.9-27.8</td><td>0.188-0.202</td></tr>
            <tr><td style="background:#444AF8;width:12px;height:10px;"></td><td>16-32%</td><td>27.8-55.7</td><td>0.202-0.230</td></tr>
            <tr><td style="background:#006400;width:12px;height:10px;"></td><td>32-64%</td><td>55.7-111</td><td>0.230-0.285</td></tr>
            <tr><td style="background:#008000;width:12px;height:10px;"></td><td>64-128%</td><td>111-223</td><td>0.285-0.397</td></tr>
            <tr><td style="background:#FFFF00;width:12px;height:10px;"></td><td>>128%</td><td>&gt;223</td><td>&gt;0.397</td></tr>
        </table>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    output_file = OUTPUT_DIR / "perseidy_full_cz.html"
    m.save(output_file)
    print("  Saved: {}".format(output_file))
    return output_file


def create_top_sites_map():
    print("Creating top sites map...")

    best_sites = pd.read_csv(BEST_SITES_CSV)
    best_sites = best_sites.sort_values('darkness_value')

    m = folium.Map(location=[49.8, 15.5], zoom_start=7, tiles='cartodb.dark_matter')

    # Add Falchi
    add_falchi_layer(m)

    # Add markers
    for idx, (_, row) in enumerate(best_sites.iterrows()):
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val):
            continue

        color = get_falchi_color(val)
        name = row.get('name', 'Unnamed POI')
        city = row['reachable_from_city']
        popup_text = u"""
        <b>{}. {}</b><br>
        <b>{}</b><br>
        Tma: {:.2f}<br>
        Lat/Lon: {:.4f}, {:.4f}
        """.format(idx+1, city, name, val, row['lat'], row['lon'])

        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color='red', icon='star', prefix='fa'),
            tooltip=u'{}. {}: {}'.format(idx+1, city, name)
        ).add_to(m)

    # Title
    title_html = u'''
    <div style="position: fixed; top: 10px; left: 10px; z-index: 1000;
                background: white; padding: 12px; border-radius: 5px;
                box-shadow: 0 0 5px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">Perseidy - Nejtemnější místa per kraj</h3>
        <p style="margin: 5px 0 0 0; font-size: 11px;">Best place per region within 1h drive</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Statistics table
    stats_rows = ""
    for idx, (_, row) in enumerate(best_sites.iterrows()):
        val = row.get('darkness_value', None)
        if val is None or pd.isna(val):
            continue
        color = get_falchi_color(val)
        stats_rows += u'''
        <tr style="background: linear-gradient(90deg, {} {}%, transparent {}%);">
            <td>{}</td>
            <td><b>{}</b></td>
            <td>{}</td>
            <td>{:.2f}</td>
        </tr>'''.format(color, int(val*50), int(val*50), idx+1, row['reachable_from_city'],
                        row.get('name', '?'), val)

    table_html = u'''
    <div style="position: fixed; bottom: 10px; left: 10px; z-index: 999;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 5px rgba(0,0,0,0.3); font-size: 11px;
                max-height: 300px; overflow-y: auto; max-width: 400px;">
        <h4 style="margin: 0 0 10px 0; font-size: 13px;">Top místa podle krajů</h4>
        <table style="border-collapse: collapse; width: 100%; font-size: 10px;">
            <tr style="border-bottom: 2px solid #333;">
                <th>#</th><th>Kraj</th><th>Místo</th><th>Tma</th>
            </tr>
            {}
        </table>
    </div>
    '''.format(stats_rows)
    m.get_root().html.add_child(folium.Element(table_html))

    # Legend with physical units
    legend_html = u'''
    <div style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 5px rgba(0,0,0,0.3); font-size: 9px;">
        <b>Falchi 2015 - Světelné znečištění</b><br>
        <table>
            <tr><th></th><th>Ratio</th><th>Artif.<br>(μcd/m²)</th><th>Total<br>(mcd/m²)</th></tr>
            <tr><td style="background:#000000;width:12px;height:10px;"></td><td>≤1%</td><td>&lt;1.74</td><td>&lt;0.176</td></tr>
            <tr><td style="background:#808080;width:12px;height:10px;"></td><td>1-2%</td><td>1.74-3.48</td><td>0.176-0.177</td></tr>
            <tr><td style="background:#A9A9A9;width:12px;height:10px;"></td><td>2-4%</td><td>3.48-6.96</td><td>0.177-0.181</td></tr>
            <tr><td style="background:#00008B;width:12px;height:10px;"></td><td>4-8%</td><td>6.96-13.9</td><td>0.181-0.188</td></tr>
            <tr><td style="background:#0000FF;width:12px;height:10px;"></td><td>8-16%</td><td>13.9-27.8</td><td>0.188-0.202</td></tr>
            <tr><td style="background:#444AF8;width:12px;height:10px;"></td><td>16-32%</td><td>27.8-55.7</td><td>0.202-0.230</td></tr>
            <tr><td style="background:#006400;width:12px;height:10px;"></td><td>32-64%</td><td>55.7-111</td><td>0.230-0.285</td></tr>
            <tr><td style="background:#008000;width:12px;height:10px;"></td><td>64-128%</td><td>111-223</td><td>0.285-0.397</td></tr>
            <tr><td style="background:#FFFF00;width:12px;height:10px;"></td><td>>128%</td><td>&gt;223</td><td>&gt;0.397</td></tr>
        </table>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    output_file = OUTPUT_DIR / "perseidy_top_sites.html"
    m.save(output_file)
    print("  Saved: {}".format(output_file))
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
