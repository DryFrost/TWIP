import rasterio
import rasterio.features
import geopandas as gpd
from shapely.geometry import shape
import os

directory = "/home/dryfrost/Desktop/HUCS"  # Replace with the directory path where the .tif files are located


def calculate_aspect_ratio(polygon):
    # Calculate the minimum bounding rectangle
    min_rect = polygon.minimum_rotated_rectangle
    
    # Get the coordinates of the rectangle's vertices
    coords = list(min_rect.exterior.coords)
    
    # Calculate the length of the sides
    side_a = ((coords[0][0] - coords[1][0]) ** 2 + (coords[0][1] - coords[1][1]) ** 2) ** 0.5
    side_b = ((coords[1][0] - coords[2][0]) ** 2 + (coords[1][1] - coords[2][1]) ** 2) ** 0.5
    
    # Calculate the aspect ratio
    return max(side_a, side_b) / min(side_a, side_b)

def calculate_polsby_popper(polygon):
    # Calculate area of the polygon
    area = polygon.area
    # Calculate perimeter of the polygon
    perimeter = polygon.length
    # Calculate Polsby-Popper compactness
    return (4 * 3.1415 * area) / (perimeter ** 2)

tif_files = []

for file in os.listdir(directory):
    if file.endswith(".tif"):
        tif_files.append(os.path.join(directory, file))


for file_path in tif_files:
    file_name_stripped = os.path.splitext(os.path.basename(file_path))[0]
    new_directory = os.path.join(directory, file_name_stripped)

    twip_path = new_directory + "/TWIP.tif"
    ShapeFilePath = new_directory + "/" + file_name_stripped + ".shp"


    # read the raster
    with rasterio.open(twip_path) as ds:
        data = ds.read(1).astype('float32')
        transform = ds.transform

    # create polygons for each feature
    shapes = list(rasterio.features.shapes(data, transform=transform))

    # convert to geopandas dataframe
    gdf = gpd.GeoDataFrame.from_features([{"geometry": shape(geom), "properties": {"value": value}} for geom, value in shapes])

    gdf.crs = 'EPSG:4269'

    gdf = gdf.to_crs('EPSG:26915')

    # keep only polygons with value 1
    gdf = gdf[gdf["value"] == 1]

    gdf['geometry'] = gdf['geometry'].buffer(100)

    merged_gdf = gdf.buffer(5).buffer(-5)

    gdf['geometry'] = gpd.GeoSeries(merged_gdf)

    # smooth polygons using the Douglas-Peucker algorithm
    tolerance = 15.0  # this value will determine the level of smoothing
    gdf["geometry"] = gdf["geometry"].simplify(tolerance)

    # compute area (in square meters assuming the data is in a metric CRS)
    gdf["area"] = gdf["geometry"].area

    # 1 acre to square meters
    acre_to_sqm = 4046.86

    # remove polygons smaller than 125 acres
    gdf = gdf[gdf["area"] >= (100 * acre_to_sqm)]

    gdf['aspect_ratio'] = gdf['geometry'].apply(calculate_aspect_ratio)

    gdf = gdf[gdf['aspect_ratio'] < 5]

    gdf['compactness'] = gdf['geometry'].apply(calculate_polsby_popper)

    gdf = gdf[gdf['compactness'] > 0.4]

    gdf = gdf.to_crs('EPSG:4269')

    # save to new shapefile
    gdf.to_file(ShapeFilePath)
