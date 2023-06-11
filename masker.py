import os
from osgeo import gdal

def create_mask(input_raster_path, output_mask_path):
    # Open the input raster
    input_raster = gdal.Open(input_raster_path)

    # Get the raster's metadata
    raster_width = input_raster.RasterXSize
    raster_height = input_raster.RasterYSize
    raster_band_count = input_raster.RasterCount

    # Create a new mask raster
    driver = gdal.GetDriverByName('GTiff')
    mask_raster = driver.Create(output_mask_path, raster_width, raster_height, 1, gdal.GDT_Byte)

    # Set the mask raster's georeferencing information
    mask_raster.SetGeoTransform(input_raster.GetGeoTransform())
    mask_raster.SetProjection(input_raster.GetProjection())

    # Get the input raster's band
    input_band = input_raster.GetRasterBand(1)

    # Create the mask using values of 0
    mask_band = mask_raster.GetRasterBand(1)
    mask_data = input_band.ReadAsArray()
    mask_data[mask_data != 0] = 255  # Set non-zero values to 255 (white)
    mask_band.WriteArray(mask_data)

    # Clean up and close the raster datasets
    input_raster = None
    mask_raster = None

    print("Raster masked successfully.")


def mask_raster_with_zero(input_raster_path, mask_path, output_masked_path):
    # Open the input raster
    input_raster = gdal.Open(input_raster_path)

    # Get the raster's metadata
    raster_width = input_raster.RasterXSize
    raster_height = input_raster.RasterYSize
    raster_band_count = input_raster.RasterCount

    # Open the mask raster
    mask_raster = gdal.Open(mask_path)

    # Create a new masked raster
    driver = gdal.GetDriverByName('GTiff')
    masked_raster = driver.Create(output_masked_path, raster_width, raster_height, raster_band_count, input_raster.GetRasterBand(1).DataType)

    # Set the masked raster's georeferencing information
    masked_raster.SetGeoTransform(input_raster.GetGeoTransform())
    masked_raster.SetProjection(input_raster.GetProjection())

    # Apply the mask to each band of the input raster
    for band_num in range(1, raster_band_count + 1):
        input_band = input_raster.GetRasterBand(band_num)
        mask_band = mask_raster.GetRasterBand(1)
        masked_band = masked_raster.GetRasterBand(band_num)

        input_data = input_band.ReadAsArray()
        mask_data = mask_band.ReadAsArray()
        masked_data = input_data * (mask_data / 255)  # Apply the mask

        masked_band.WriteArray(masked_data)

    # Clean up and close the raster datasets
    input_raster = None
    mask_raster = None
    masked_raster = None

    print("Raster masked successfully.")


directory = "/home/dryfrost/Desktop/HUCS"  # Replace with the directory path where the .tif files are located

tif_files = []

for file in os.listdir(directory):
    if file.endswith(".tif"):
        tif_files.append(os.path.join(directory, file))


for file_path in tif_files:
    file_name_stripped = os.path.splitext(os.path.basename(file_path))[0]
    new_directory = os.path.join(directory, file_name_stripped)
    os.makedirs(new_directory, exist_ok=True)
    


#input_raster_path = "/home/dryfrost/Desktop/HUCS/Upper Chariton.tif"
#output_mask_path = "/home/dryfrost/Desktop/HUCS/Upper Chariton/mask.tif"
#create_mask(input_raster_path, output_mask_path)

#toBeMasked = "/home/dryfrost/Desktop/HUCS/Upper Chariton/flow_accumulation.tif"
#mask_path = "/home/dryfrost/Desktop/HUCS/Upper Chariton/mask.tif"
#output = "/home/dryfrost/Desktop/HUCS/Upper Chariton/flow_accumulation.tif"
mask_raster_with_zero(input_raster_path, mask_path, output)






