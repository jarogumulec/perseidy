#!/usr/bin/env python3
"""
Crop the Falchi World Atlas of Night Sky Brightness GeoTIFF to Czech Republic bounds.
Uses the polygon from prac_obrys_cesko.geojson as mask.
"""

from pathlib import Path
import geopandas as gpd
from rasterio import open as rio_open
from rasterio.mask import mask

# Paths
INPUT_TIFF = "World_Atlas_2015.tif"
CZ_POLYGON_GEOJSON = "prac_obrys_cesko.geojson"
OUTPUT_TIFF = str(Path(__file__).parent / "data" / "cesko_tma.tif")


def main():
    # Load CZ polygon, ensure EPSG:4326
    gdf = gpd.read_file(CZ_POLYGON_GEOJSON)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    # Get polygon geometries (filter for Polygon type only)
    geometries = []
    for geom in gdf.geometry:
        if geom.geom_type in ['Polygon', 'MultiPolygon']:
            geometries.append(geom)

    if not geometries:
        print("ERROR: No polygon geometry found in GeoJSON")
        return

    print(f"Found {len(geometries)} polygon(s) to use as mask")

    # Open raster and crop
    print(f"Reading input TIFF: {INPUT_TIFF}")
    with rio_open(INPUT_TIFF) as src:
        out_image, out_transform = mask(src, geometries, crop=True, all_touched=True)
        out_meta = src.meta.copy()

    # Update metadata
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "nodata": 0  # Use 0 for NoData (oceans/outside area)
    })

    # Write output
    import os
    os.makedirs(os.path.dirname(OUTPUT_TIFF), exist_ok=True)

    print(f"Writing cropped TIFF: {OUTPUT_TIFF}")
    with rio_open(OUTPUT_TIFF, "w", **out_meta) as dest:
        dest.write(out_image)

    print(f"\nCropped TIFF saved to: {OUTPUT_TIFF}")
    print(f"Original size: ~3GB, Cropped size: should be ~50-100MB")


if __name__ == "__main__":
    main()
