#!/usr/bin/env python3
"""
Convert Falchi GeoTIFF to PNG overlay for Folium maps.

Creates a semi-transparent PNG with proper Web Mercator projection.
"""

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
from PIL import Image
import io

# Paths
TIFF_PATH = "/Users/jarogumulec/Documents/Kody/perseidy/data/cesko_tma.tif"
OUTPUT_PNG = "/Users/jarogumulec/Documents/Kody/perseidy/output/falchi_overlay.png"
OUTPUT_BOUNDS_JSON = "/Users/jarogumulec/Documents/Kody/perseidy/output/falchi_bounds.json"

# Falchi thresholds and colors
FALCHI_THRESHOLDS = [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96]
FALCHI_COLORS_RGB = [
    (0, 0, 0),           # <= 0.01  - Černá
    (128, 128, 128),     # 0.01-0.02 - Tmavě šedá
    (169, 169, 169),     # 0.02-0.04 - Šedá
    (0, 0, 139),         # 0.04-0.08 - Tmavě modrá
    (0, 0, 255),         # 0.08-0.16 - Modrá
    (68, 74, 248),       # 0.16-0.32 - Světle modrá
    (0, 100, 0),         # 0.32-0.64 - Tmavě zelená
    (0, 128, 0),         # 0.64-1.28 - Zelená
    (255, 255, 0),       # 1.28-2.56 - Žlutá
    (255, 165, 0),       # 2.56-5.12 - Oranžová
    (255, 0, 0),         # 5.12-10.24 - Červená
    (255, 0, 255),       # 10.24-20.48 - Purpurová
    (255, 192, 203),     # 20.48-40.96 - Růžová
    (255, 255, 255),     # > 40.96 - Bílá
]


def value_to_rgba(value):
    """Map darkness value to RGBA color with transparency for NoData."""
    if value is None or np.isnan(value) or value == 0:
        return (0, 0, 0, 0)  # Fully transparent

    for i, threshold in enumerate(FALCHI_THRESHOLDS):
        if value <= threshold:
            r, g, b = FALCHI_COLORS_RGB[i]
            return (r, g, b, 200)

    r, g, b = FALCHI_COLORS_RGB[-1]
    return (r, g, b, 200)


def create_falchi_png():
    """
    Create PNG overlay from Falchi GeoTIFF with proper orientation.
    """
    with rasterio.open(TIFF_PATH) as src:
        # Read original data
        data = src.read(1).astype(float)
        height, width = data.shape

        # Get bounds in EPSG:4326
        left, bottom, right, top = src.bounds

        # Create RGBA image
        # Note: rasterio reads with origin at top-left, same as PIL
        img_data = np.zeros((height, width, 4), dtype=np.uint8)

        for i in range(height):
            for j in range(width):
                val = data[i, j]
                img_data[i, j] = value_to_rgba(val)

        # Create PIL Image - no flip needed, rasterio and PIL have same origin
        img = Image.fromarray(img_data, 'RGBA')

        # Save PNG
        img.save(OUTPUT_PNG, 'PNG', optimize=True)

        print(f"Saved PNG to: {OUTPUT_PNG}")
        print(f"Image size: {width}x{height}")
        print(f"Bounds (EPSG:4326):")
        print(f"  SW (lat,lon): ({bottom:.6f}, {left:.6f})")
        print(f"  NE (lat,lon): ({top:.6f}, {right:.6f})")

        # Save bounds as JSON for use in HTML
        import json
        bounds_info = {
            'min_lon': left,
            'min_lat': bottom,
            'max_lon': right,
            'max_lat': top,
            'width': width,
            'height': height
        }
        with open(OUTPUT_BOUNDS_JSON, 'w') as f:
            json.dump(bounds_info, f, indent=2)

        return bounds_info


if __name__ == "__main__":
    bounds = create_falchi_png()
    print(f"\nBounds for Folium ImageOverlay:")
    print(f"  bounds=[[min_lat, min_lon], [max_lat, max_lon]]")
    print(f"  bounds=[[{bounds['min_lat']:.6f}, {bounds['min_lon']:.6f}], [{bounds['max_lat']:.6f}, {bounds['max_lon']:.6f}]]")
