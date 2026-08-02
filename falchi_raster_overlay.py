#!/usr/bin/env python3
"""
Convert Falchi GeoTIFF to PNG overlay for Folium maps.

Creates a semi-transparent PNG that can be added as an ImageOverlay.
"""

import rasterio
import numpy as np
from PIL import Image
import io
import base64


# Falchi color palette (RGB) - matches QGIS export
FALCHI_PALETTE = [
    (0, 0, 0),       # <= 0.01  - Černá
    (128, 128, 128), # 0.01-0.02 - Tmavě šedá
    (169, 169, 169), # 0.02-0.04 - Šedá
    (0, 0, 139),     # 0.04-0.08 - Tmavě modrá
    (0, 0, 255),     # 0.08-0.16 - Modrá
    (68, 74, 248),   # 0.16-0.32 - Světle modrá
    (0, 100, 0),     # 0.32-0.64 - Tmavě zelená
    (0, 128, 0),     # 0.64-1.28 - Zelená
    (255, 255, 0),   # 1.28-2.56 - Žlutá
    (255, 165, 0),   # 2.56-5.12 - Oranžová
    (255, 0, 0),     # 5.12-10.24 - Červená
    (255, 0, 255),   # 10.24-20.48 - Purpurová
    (255, 192, 203), # 20.48-40.96 - Růžová
    (255, 255, 255), # > 40.96 - Bílá
]

FALCHI_THRESHOLDS = [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96]


def value_to_color(value):
    """Map darkness value to RGB color."""
    if value is None or np.isnan(value):
        return (0, 0, 0, 0)  # Transparent for no data

    for i, threshold in enumerate(FALCHI_THRESHOLDS):
        if value <= threshold:
            r, g, b = FALCHI_PALETTE[i]
            return (r, g, b, 200)  # 200 = ~78% opacity

    # Above 40.96
    r, g, b = FALCHI_PALETTE[-1]
    return (r, g, b, 200)


def create_falchi_overlay(tiff_path, opacity=0.6):
    """
    Create a PNG overlay from Falchi GeoTIFF.

    Returns:
        tuple: (png_base64, bounds) where bounds is (minx, miny, maxx, maxy)
    """
    with rasterio.open(tiff_path) as src:
        # Read the raster data
        data = src.read(1)  # First band
        transform = src.transform
        bounds = src.bounds

        # Get CRS and convert to Web Mercator if needed
        if src.crs.to_epsg() == 4326:
            # Transform bounds to Web Mercator (EPSG:3857)
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
            minx, miny = transformer.transform(bounds.left, bounds.bottom)
            maxx, maxy = transformer.transform(bounds.right, bounds.top)
            bounds_3857 = (minx, miny, maxx, maxy)
        else:
            bounds_3857 = (bounds.left, bounds.bottom, bounds.right, bounds.top)

        # Apply colormap
        height, width = data.shape

        # Create RGBA image
        img_data = np.zeros((height, width, 4), dtype=np.uint8)

        for i in range(height):
            for j in range(width):
                val = data[i, j]
                if val is not None and not np.isnan(val):
                    img_data[i, j] = value_to_color(val)
                else:
                    img_data[i, j] = (0, 0, 0, 0)  # Fully transparent

        # Convert to PIL Image and flip (rasterio has origin at top-left)
        img = Image.fromarray(img_data, 'RGBA')
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        # Save to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        png_bytes = buffer.getvalue()

        # Encode to base64
        png_base64 = base64.b64encode(png_bytes).decode('utf-8')

        return png_base64, bounds_3857


def create_html_snippet(png_base64, bounds, opacity=0.5):
    """Create HTML/JS snippet for displaying Falchi overlay using Leaflet image overlay."""
    minx, miny, maxx, maxy = bounds

    html = f'''
    <!-- Falchi Light Pollution Overlay -->
    <script>
        var falchiImage = L.imageOverlay(
            'data:image/png;base64,{png_base64}',
            [[{miny}, {minx}], [{maxy}, {maxx}]],
            {{opacity: {opacity}}}
        ).addTo(map);

        // Add to layer control if available
        if (typeof layerControl !== 'undefined') {{
            falchiImage.addTo(layerControl.getLayers()[0]);
        }}
    </script>
    '''
    return html


if __name__ == "__main__":
    import sys

    tiff_path = "/Users/jarogumulec/Documents/Kody/perseidy/data/cesko_tma.tif"

    print("Creating Falchi overlay...")
    png_base64, bounds = create_falchi_overlay(tiff_path, opacity=0.6)

    print(f"Bounds (EPSG:3857): {bounds}")
    print(f"PNG size: {len(png_base64)} bytes ({len(png_base64)/1024:.1f} KB)")

    # Save to file for use in maps
    output_path = "/Users/jarogumulec/Documents/Kody/perseidy/output/falchi_overlay.png"
    with open(output_path, 'wb') as f:
        f.write(base64.b64decode(png_base64))
    print(f"Saved PNG to: {output_path}")

    # Print bounds for use in Folium
    print(f"\nUse these bounds in Folium:")
    print(f"  min_lat, min_lon = {bounds[1]:.6f}, {bounds[0]:.6f}")
    print(f"  max_lat, max_lon = {bounds[3]:.6f}, {bounds[2]:.6f}")
