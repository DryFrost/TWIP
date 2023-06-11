import os
from pysheds.grid import Grid
import rasterio
import numpy as np
from scipy.ndimage import filters
from scipy.ndimage import generic_filter

directory = "/home/dryfrost/Desktop/HUCS"  # Replace with the directory path where the .tif files are located



def calculate_slope(dem):
    """
    Calculate slope 
    """
    # Calculate slope
    x, y = np.gradient(dem)
    slope_rad = np.arctan(np.sqrt(x*x + y*y))
    slope = np.degrees(slope_rad) * 0.01745

    return slope

def calculate_twi(acc,slope):
    twi = np.log(acc / np.where(slope == 0, 0.00001, np.tan(slope))) * 100

    reclassified_twi = np.zeros_like(twi)

    reclassified_twi[(twi >= -1219.681274) & (twi <= 999)] = 0
    reclassified_twi[(twi >= 1000) & (twi <= 9000)] = 1

    filtered_twi = filters.maximum_filter(reclassified_twi, size=3)

    return filtered_twi

def majority_filter(in_array):
    unique, counts = np.unique(in_array, return_counts=True)
    if len(unique) == 0:
        return in_array[1, 1]  # return the center value if no data
    return unique[np.argmax(counts)]

def calculate_dep(dem_data,filled_dem_data):
    dem_diff_100 = (filled_dem_data - dem_data) * 100
    
    #reclassify
    dem_diff_100[dem_diff_100 <= 9] = 0
    dem_diff_100[(dem_diff_100 > 9) & (dem_diff_100 <= 24)] = 1
    dem_diff_100[(dem_diff_100 > 24) & (dem_diff_100 <= 255)] = 2

    dep_maj_filter = generic_filter(dem_diff_100, majority_filter, size=(3, 3))

    selected_dep_raster = np.where(dep_maj_filter == 2, dep_maj_filter, np.nan)

    return selected_dep_raster


tif_files = []

for file in os.listdir(directory):
    if file.endswith(".tif"):
        tif_files.append(os.path.join(directory, file))


for file_path in tif_files:
    file_name_stripped = os.path.splitext(os.path.basename(file_path))[0]
    new_directory = os.path.join(directory, file_name_stripped)
    os.makedirs(new_directory, exist_ok=True)
    with rasterio.open(file_path) as dem_dataset:
        
        #Create a PySheds instance and define the grid
        grid = Grid.from_raster(file_path)
        dem = grid.read_raster(file_path)
        
        #Fill pits in DEM
        pit_filled_dem = grid.fill_pits(dem)

        #Fill depressions in DEM
        flooded_dem = grid.fill_depressions(pit_filled_dem)

        #Resolve flats in DEM
        inflated_dem = grid.resolve_flats(flooded_dem)

        # Determine D8 flow directions from DEM
        # ----------------------
        # Specify directional mapping
        dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
            
        # Compute flow directions
        # -------------------------------------
        fdir = grid.flowdir(inflated_dem, dirmap=dirmap)

        # Calculate flow accumulation

        acc = grid.accumulation(fdir, dirmap=dirmap)

        # Calculate Slope
        slope = calculate_slope(dem)

        #calculate TWI
        TWI = calculate_twi(acc,slope)

        dep = calculate_dep(dem,flooded_dem)

        TWIP = np.logical_and(dep == 2, TWI == 1)
        
        #Save the flow accumulation raster using rasterio
        flow_accumulation_path = new_directory + "/flow_accumulation.tif"
        filled_path = new_directory + "/filled.tif"
        twip_path = new_directory + "/TWIP.tif"

        grid.to_raster(acc,flow_accumulation_path,apply_output_mask=True,blockxsize=16,blockysize=16)
        grid.to_raster(flooded_dem,filled_path,apply_output_mask=True,blockxsize=16,blockysize=16)


    with rasterio.open(
        twip_path,
        'w',
        driver='GTiff',
        width=dem_dataset.width,
        height=dem_dataset.height,
        count=1,
        crs=dem_dataset.crs,
        transform=dem_dataset.transform,
        dtype='float64'
    ) as output_dataset:
        output_dataset.write(TWIP,1)

    grid = None
    dem = None
    pit_filled_dem = None
    flooded_dem = None
    inflated_dem = None
    dirmap = None
    fdir = None
    acc = None
    slope = None
    TWI = None
    flow_accumulation_path = None
    dem_path = None
    filled_path = None
    dem_dataset = None
