import os
import rasterio
import numpy as np
from rasterio import open as rio_open
from rasterio.enums import Resampling

year = 2002
res = "9KM"
# res = "30KM"

for year in range(1997, 2025):
    # list of tiffs for one year - temp
    files_T = []
    # Specify paths where temperature data is stored
    files_T.extend([os.path.join("PATH_TO_TEMP_DATA_1", str(year), f) 
                    for f in os.listdir(os.path.join("PATH_TO_TEMP_DATA_1", str(year))) if f.endswith('.tif')])
    files_T.extend([os.path.join("PATH_TO_TEMP_DATA_2", str(year), f) 
                    for f in os.listdir(os.path.join("PATH_TO_TEMP_DATA_2", str(year))) if f.endswith('.tif')])
    
    # create stack of one year - temp
    rs_T = [rio_open(f) for f in files_T]
    
    # list of tiffs for one year - precipitation
    files_P = []
    # Specify paths where precipitation data is stored
    files_P.extend([os.path.join("PATH_TO_PRECIP_DATA_1", str(year), f) 
                    for f in os.listdir(os.path.join("PATH_TO_PRECIP_DATA_1", str(year))) if f.endswith('.tif')])
    files_P.extend([os.path.join("PATH_TO_PRECIP_DATA_2", str(year), f) 
                    for f in os.listdir(os.path.join("PATH_TO_PRECIP_DATA_2", str(year))) if f.endswith('.tif')])
    
    # create stack of one year - precipitation
    rs_P = [rio_open(f) for f in files_P]
    
    # calculate sum of temperatures for actual decade and 3 previous decades - for each 10 day period
    TEMP = np.sum(np.array([r.read(1) for r in rs_T]), axis=0)
    
    # calculate sum of total precipitation for actual decade and 3 previous decades - for each 10 day period
    OPAD = np.sum(np.array([r.read(1) for r in rs_P]), axis=0)
    
    # calculate HTC for each decade over the year
    HTC = OPAD / TEMP
    # exclude decades with NA
    HTC = np.where(np.isnan(HTC), np.nan, HTC)
    
    # save raster - each band is each decade
    output_path = f"PATH_TO_SAVE_HTC/HTC_{res}/HTC_{year}.tif"
    with rio_open(output_path, 'w', driver='GTiff', height=HTC.shape[0], width=HTC.shape[1], count=1, dtype='float32') as dst:
        dst.write(HTC, 1)

# directory - yearly mean HTC
htc_dir = "PATH_TO_HTC_DATA/"
# list of all tiffs
htc_list = [os.path.join(htc_dir, f) for f in os.listdir(htc_dir) if f.endswith('.tif')]

htc_years = list(range(2001, 2025))
htc_list = [f for f in htc_list if f[4:8] in map(str, htc_years)]

# create stack
htc_MULTI = [rio_open(f) for f in htc_list]

# calculate multiyear median of HTC - mean of yearly HTC
HTC_MEDIAN = np.median(np.array([r.read(1) for r in htc_MULTI]), axis=0)
# 0 to NA
HTC_MEDIAN[HTC_MEDIAN < 0] = np.nan

# save raster
output_median_path = f"PATH_TO_SAVE_MEDIAN/HTC_median_{htc_years[0]}_{htc_years[-1]}.tif"
with rio_open(output_median_path, 'w', driver='GTiff', height=HTC_MEDIAN.shape[0], width=HTC_MEDIAN.shape[1], count=1, dtype='float32') as dst:
    dst.write(HTC_MEDIAN, 1)
