# ----------------------------------------------------------
# Python script performs the following:
# - Opens and processes TCI files for drought mapping with DISS formula
# - Reads input satellite data and median HTC with the era5_htc_30_median.img file
# - Masks major arable and meadow lands using the meadow_arable_mask_snap.img file
# - Saves the final data to specific formats (e.g., GeoTIFF)
#
# Requirements:
# - Python with libraries: os, glob, numpy, rasterio, and GDAL
# - Ensure input files (era5_htc_30_median.img, meadow_arable_mask_snap.img, and tci) are in the working directory
# - In order to specify coefficients please read the research papers 
#   https://doi.org/10.3390/rs12182944
#   https://doi.org/10.1109/IGARSS47720.2021.9553739
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
import numpy as np
from osgeo import gdal
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# Set paths
home_path = "D:/FPCUP BALTIC/"
tci_path = "D:/FPCUP BALTIC/TCI/"
path_out = "D:/FPCUP BALTIC/DISS/"

year = "2022"  # Adjust the year as necessary
dekad = ["05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]

# Coefficients to be specified for the DISS formula
a = ?.?  # please set coefficient value for n1_memory
b = ?.?  # please set coefficient value for n2_memory
c = ?.?  # please set coefficient value for n3_memory
diss_base = ?.?  # please set base value for DISS formula
exp_factor = ?.?  # please set exponent base value

# Helper function to read raster
def read_raster(file_path):
    dataset = gdal.Open(file_path)
    return dataset.ReadAsArray(), dataset.GetGeoTransform(), dataset.GetProjection()

# Helper function to write raster
def write_raster(output_path, data, geo_transform, projection):
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_path, data.shape[1], data.shape[0], 1, gdal.GDT_Float32)
    out_ds.SetGeoTransform(geo_transform)
    out_ds.SetProjection(projection)
    out_ds.GetRasterBand(1).WriteArray(data)
    out_ds.FlushCache()

# Function for processing one year and dekad combination
def process_year_dekad(year, dekad):
    for d in dekad:
        # File paths for TCI and other datasets
        ftci1 = tci_path + "tci" + year + d + ".img"
        ftci2 = tci_path + "tci" + year + str(int(d)-1).zfill(2)  # previous dekad
        ftci3 = tci_path + "tci" + year + str(int(d)-2).zfill(2)  # two dekads ago
        
        fout = path_out + "diss_" + year + d + ".tif"
        fout_kl = path_out + "diss_" + year + d + "_kl.tif"

        # Read input rasters
        n1_tci1, geo_transform, projection = read_raster(ftci1)
        n2_tci2, _, _ = read_raster(ftci2)
        n3_tci3, _, _ = read_raster(ftci3)
        n5_siel40median, _, _ = read_raster("D:/FPCUP BALTIC/era5_htc_30_median.img") #HTC median file to be delivered from ERA5-Land product
        n6_mask, _, _ = read_raster("D:/FPCUP BALTIC/meadow_arable_mask_snap.img") #meadows and arable lands mask file

        # Apply calculations for the 'diss' raster
        n1_memory = np.where(n1_tci1 <= 101, n1_tci1, 50)
        n2_memory = np.where(n2_tci2 <= 101, n2_tci2, 0.5 * (n1_tci1 + n3_tci3))
        n3_memory = np.where(n3_tci3 <= 101, n3_tci3, 50)

        # DISS formula (with coefficients a, b, c)
        n4_diss = (n5_siel40median - diss_base) * np.exp(2 * (exp_factor + a * n1_memory + b * n2_memory + c * n3_memory))

        # Apply the mask
        n4_diss = np.where(n6_mask == 1, n4_diss, -1)

        # Write output raster for 'diss'
        write_raster(fout, n4_diss, geo_transform, projection)

        # Apply classification to 'diss' values
        n2_diss_kl = np.digitize(n4_diss, bins=[0.0, 0.5, 0.8, 1.5, 5.0, np.inf])
        write_raster(fout_kl, n2_diss_kl, geo_transform, projection)

        # Apply color table
        apply_color_table(n2_diss_kl, year, d)

        print(f"Processing complete for {year}-{d}")

# Function to apply color table
def apply_color_table(raster_data, year, d):
    # For visualization (coloring)
    cmap = ListedColormap(['#0000FF', '#00FF00', '#FFFF00', '#FF0000', '#FF00FF'])  # Example colors
    fig, ax = plt.subplots()
    cax = ax.imshow(raster_data, cmap=cmap)
    fig.colorbar(cax)

    # Save the colored output
    color_output = path_out + "diss_kl_color_" + year + d + ".png"
    plt.savefig(color_output)
    plt.close(fig)

# Main function to process the year and dekads
def main():
    print("Starting processing...")
    process_year_dekad(year, dekad)
    print("Processing complete!")

if __name__ == "__main__":
    main()
