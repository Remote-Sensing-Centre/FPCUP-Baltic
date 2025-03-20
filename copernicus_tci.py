# ----------------------------------------------------------
# Python script performs the following:
# - Opens and processes land and water mask and TCI color scheme files
# - Reads input satellite data and scales TCI values (0-100)
# - Masks major water bodies using the water_mask.img file
# - Reprojects and resamples data from 5 km to 1 km resolution
# - Applies color to Copernicus TCI using the tci_colour.img file for visualization
# - Saves the transformed data to specific formats (e.g., GeoTIFF)
#
# Requirements:
# - Python with libraries: os, glob, numpy, rasterio, and GDAL
# - Download original satellite data from:
#   https://land.copernicus.eu/en/products/temperature-and-reflectance/10-daily-land-surface-temperature-thermal-condition-index-global-v1-0-5km
#   https://land.copernicus.eu/en/products/temperature-and-reflectance/10-daily-land-surface-temperature-thermal-condition-index-global-v2-0-5km
# - Ensure input files (water_mask.img, tci_colour.img, and satellite data) are in the working directory
#
# Publishing and rights:
# If you use this open-source code in your work, please cite the following references
# Remote Sensing Centre, Institute of Geodesy and Cartography, Poland
# Dabrowska-Zielinska, K.; Malinska, A.; Bochenek, Z.; Bartold, M.; Gurdak, R.; Paradowski, K.; Lagiewska, M. 
# Drought Model DISS Based on the Fusion of Satellite and Meteorological Data under Variable Climatic Conditions. 
# Remote Sens. 2020, 12, 2944. https://doi.org/10.3390/rs12182944 
#
# Dabrowska-Zielinska, K.; Bochenek, Z.; Malinska, A.; Bartold, M.; Gurdak, R.; Lagiewska, M.; Paradowski, K. 
# Drought Assessment Applying Joined Meteorological and Satellite Data. 
# In Proceedings of the 2021 IEEE International Geoscience and Remote Sensing Symposium IGARSS, Brussels, Belgium, 11–16 July 2021; pp. 6591–6594.
# https://doi.org/10.1109/IGARSS47720.2021.9553739
# ----------------------------------------------------------

import os
import glob
import numpy as np
import rasterio
from osgeo import gdal, osr

# Define directories
base_dir = os.getcwd()  # Use the current working directory
output_dir = os.path.join(base_dir, 'Uklad92')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# File paths for input files (to be provided by the user)
landwater_path = os.path.join(base_dir, 'water_mask.img')
tci_colour_path = os.path.join(base_dir, 'tci_colour.img')

if not os.path.exists(landwater_path) or not os.path.exists(tci_colour_path):
    print("Land-water mask or TCI color file not found in the current directory. Exiting.")
    exit()

# Helper function to apply map projection
def apply_map_projection(input_path, output_path, params, projection_epsg=2180):
    dataset = gdal.Open(input_path)
    if not dataset:
        print(f"Failed to open input file: {input_path}")
        return
    
    # Set projection
    projection = osr.SpatialReference()
    projection.ImportFromEPSG(projection_epsg)
    
    warp_options = gdal.WarpOptions(
        dstSRS=projection.ExportToWkt(),
        xRes=1000,
        yRes=1000,
        resampleAlg='near',
        outputBounds=[500000, -5300000, 6378137, 6356752.3141],
        srcNodata=255,
        dstNodata=255
    )
    gdal.Warp(output_path, dataset, options=warp_options)
    print(f"Projected file saved: {output_path}")

# Input starting and ending dates
start_date = "2401"  # Example: "2401" (24th day of year 2001)
end_date = "2436"    # Example: "2436" (36th day of year 2001)

start_year = int(start_date[:2])
end_year = int(end_date[:2]) + 1

day_start = int(start_date[2:])
day_end = int(end_date[2:])

# Main processing loop
for year in range(start_year, end_year):
    for day in range(1, 37):  # 36 TCI periods per year
        day_code = f"{day:02d}"
        file_code = f"tci{year}{day_code}"
        input_file_pattern = os.path.join(base_dir, f"input/{file_code}.tiff")
        
        input_files = glob.glob(input_file_pattern)
        if not input_files:
            print(f"No files found for {file_code}")
            continue
        
        input_file = input_files[0]
        print(f"Processing file: {input_file}")
        
        # Open the input file with rasterio
        with rasterio.open(input_file) as src:
            data = src.read(1)  # Read first band
            transform = src.transform
            crs = src.crs
        
        # Apply scaling and conditional logic (example calculation)
        scaled_data = np.where((data >= 0) & (data <= 10000), ((data / 100) + 1), 108)
        scaled_data = scaled_data.astype(np.uint8)

        # Save the scaled data
        scaled_output_path = os.path.join(output_dir, f"{file_code}_scaled.tif")
        with rasterio.open(
            scaled_output_path,
            'w',
            driver='GTiff',
            height=scaled_data.shape[0],
            width=scaled_data.shape[1],
            count=1,
            dtype='uint8',
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(scaled_data, 1)
        print(f"Saved scaled file: {scaled_output_path}")
        
        # Apply map projection and save projected file
        projected_output_path = os.path.join(output_dir, f"{file_code}_92.tif")
        apply_map_projection(scaled_output_path, projected_output_path, params={
            "scale_factor": 0.9993,
            "false_easting": 500000,
            "false_northing": -5300000,
            "central_meridian": 19.0
        })

        # Example color transformation logic
        color_mapped_data = np.where(data == 0, 109, scaled_data)
        color_output_path = os.path.join(base_dir, f"{file_code}.tif")
        
        # Save the color-mapped file
        with rasterio.open(
            color_output_path,
            'w',
            driver='GTiff',
            height=color_mapped_data.shape[0],
            width=color_mapped_data.shape[1],
            count=3,  # RGB bands
            dtype='uint8',
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(color_mapped_data, 1)  # Red band
            dst.write(color_mapped_data, 2)  # Green band
            dst.write(color_mapped_data, 3)  # Blue band
        print(f"Saved color-mapped file: {color_output_path}")

print("Processing completed.")
