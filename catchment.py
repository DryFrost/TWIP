import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom, transform
from pyproj import Transformer
import numpy as np
import fiona
from pysheds.grid import Grid
from shapely.geometry import Point
import os
import pandas as pd

directory = "/home/dryfrost/Desktop/HUCS"  # Replace with the directory path where the .tif files are located

tif_files = []

points_gdf = gpd.GeoDataFrame()

for file in os.listdir(directory):
    if file.endswith(".tif"):
        tif_files.append(os.path.join(directory, file))


for file_path in tif_files:
    file_name_stripped = os.path.splitext(os.path.basename(file_path))[0]
    new_directory = os.path.join(directory, file_name_stripped)

    raster_path = new_directory + "/flow_accumulation.tif"
    shapefile_path = new_directory + "/" + file_name_stripped + ".shp"
    catch_path = new_directory + "/catchments"
    new_directory_2 = os.path.join(new_directory,catch_path)
    os.makedirs(new_directory_2, exist_ok=True)


    # Read the shapefile containing polygons
    polygons = gpd.read_file(shapefile_path)

    # Read the raster file containing flow accumulation values
    raster = rasterio.open(raster_path)

    # Instantiate grid from raster
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
    acc = grid.accumulation(fdir, dirmap=dirmap)

    # Iterate through each polygon
    for idx, polygon in polygons.iterrows():
        a = grid
        # Extract the polygon's geometry
        geometry = polygon.geometry

        # Clip the raster using the polygon's geometry
        clipped_raster, transform = mask(raster, [geometry], crop=True)

        pixel_coords = np.unravel_index(np.argmax(clipped_raster), clipped_raster.shape)

        lon, lat = rasterio.transform.xy(transform, pixel_coords[1], pixel_coords[2])

        # Transform the geometry back to the original CRS for printing

        # Print the coordinates
        print(f"Polygon {idx}: Highest Flow Accumulation - Lat: {lat}, Lon: {lon}")

        point_geom = Point(lon,lat)

        point_gdf = gpd.GeoDataFrame({'flow_accumulation': 'HI',
                                  'geometry': [point_geom],
                                  'polygon_id': [idx]},
                                 crs=raster.crs)
        points_gdf = pd.concat([points_gdf, point_gdf], ignore_index=True)

        x_snap, y_snap = a.snap_to_mask(acc > 1000, (lon,lat))

        catch = a.catchment(x=x_snap,y=y_snap,fdir=fdir,dirmap=dirmap,xytype='coordinate')

        #a.clip_to(catch)

        catch_view = a.view(catch,dtype=np.uint8)

        shapes = a.polygonize(catch_view)

        schema = {
        'geometry': 'Polygon',
        'properties': {'LABEL': 'float:16'}
        }

        shapefile_out_path = catch_path + "/" + str(idx) +".shp"

        # Write shapefile
        with fiona.open(shapefile_out_path, 'w',
                        driver='ESRI Shapefile',
                        crs=a.crs.srs,
                        schema=schema) as c:
            i = 0
            for shape, value in shapes:
                rec = {}
                rec['geometry'] = shape
                rec['properties'] = {'LABEL' : str(value)}
                rec['id'] = str(i)
                if value == 1:
                    c.write(rec)
                i += 1

output_shapefile = '/home/dryfrost/Desktop/CATCHPOINTS.shp'
points_gdf.to_file(output_shapefile)


