import geopandas as gpd
import pandas as pd
import numpy as np
import multiprocessing
import json

from shapely.geometry import Polygon
from shapely.ops import unary_union

"""
    1. Create Minimum Bounding Rectangle (MBR) ###
"""
def create_mbr(data):
    # Create minimum bounding rectangles for each polygon
    mbr_geometries = []

    for fid, geometry in enumerate(data['geometry']):
        if geometry.geom_type == 'Polygon':
            mbr = gpd.GeoDataFrame(geometry=[geometry.minimum_rotated_rectangle])
            mbr['id'] = fid  # Add FID attribute
            mbr_geometries.append(mbr)

    # Concatenate the list of GeoDataFrames into a single GeoDataFrame
    mbr_gdf = gpd.GeoDataFrame(pd.concat(mbr_geometries, ignore_index=True))

    return mbr_gdf

"""
    2. Generate Grids ###
"""
def calculate_angles(rectangle_coords):
    angles = []

    for i in range(4):
        x1, y1 = rectangle_coords[i]
        x2, y2 = rectangle_coords[(i + 1) % 4]

        angle_rad = np.arctan2(y2 - y1, x2 - x1)
        angle_deg = np.degrees(angle_rad)

        angles.append(angle_deg)

    return angles


def create_rotated_grid(polygon, grid_size, rotation_angle, fid):
    xmin, ymin, xmax, ymax = polygon.bounds
    rows = int(np.ceil((ymax - ymin) / grid_size))
    cols = int(np.ceil((xmax - xmin) / grid_size))

    centroid = polygon.centroid

    grid_data = {'geometry': [], 'id': []}
    for i in range(cols):
        for j in range(rows):
            left = xmin + i * grid_size
            right = xmin + (i + 1) * grid_size
            bottom = ymin + j * grid_size
            top = ymin + (j + 1) * grid_size

            grid_polygon = Polygon([(left, bottom), (right, bottom), (right, top), (left, top)])
            if grid_polygon.intersects(polygon):
                intersection = grid_polygon.intersection(polygon)
                if not intersection.is_empty:
                    grid_data['geometry'].append(intersection)
                    grid_data['id'].append(fid)

    return grid_data


def generate_grid(gdf, data_crs, grid_size):
    # Generate Grids
    grid_data_list = {'geometry': [], 'id': []}
    for index, row in gdf.iterrows():
        if row['geometry'].geom_type == 'Polygon':
            polygon = row['geometry']

            # Read FID
            fid = row['id']
            # print(fid)

            # Read coordinates
            coordinates_list = list(polygon.exterior.coords)

            # Calculate rotation angle
            rotation_angle = calculate_angles(coordinates_list)
            if rotation_angle[0] >= 50 or rotation_angle[0] <= -50:
                rotation_angle = rotation_angle[1]
            else:
                rotation_angle = rotation_angle[0]

            # Define cols based on grid size and bounding box
            xmin, ymin, xmax, ymax = polygon.bounds
            cols = int(np.ceil((xmax - xmin) / grid_size))
            rows = int(np.ceil((ymax - ymin) / grid_size))

            for i in range(cols):
                for j in range(rows):
                    left = xmin + i * grid_size
                    right = xmin + (i + 1) * grid_size
                    bottom = ymin + j * grid_size
                    top = ymin + (j + 1) * grid_size

                    grid_polygon = Polygon([(left, bottom), (right, bottom), (right, top), (left, top)])
                    if grid_polygon.intersects(polygon):
                        intersection = grid_polygon.intersection(polygon)
                        if not intersection.is_empty:
                            grid_data_list['geometry'].append(intersection)
                            grid_data_list['id'].append(fid)

    # Create a GeoDataFrame from the grid data
    grid_polygons_gdf = gpd.GeoDataFrame(grid_data_list, columns=['geometry', 'id'])

    grid_polygons_gdf.crs = data_crs

    return grid_polygons_gdf



"""
    3. Grid Selection ###
"""
def check_the_data(args):
    index, feature1, gdf2, spatial_index, gdf1_crs = args
    possible_matches_index = list(spatial_index.intersection(feature1['geometry'].bounds))
    possible_matches = gdf2.iloc[possible_matches_index]
    candidates = possible_matches[possible_matches.intersects(feature1['geometry'])]
    overlap_area = candidates.geometry.to_crs(gdf1_crs).area.sum()
    return index, overlap_area

def calculate_overlap_area_per_feature(gdf1: gpd.GeoDataFrame, gdf2):
    # Create a spatial index for gdf2
    spatial_index = gdf2.sindex

    # Reproject gdf2 to match the CRS of gdf1
    gdf1_crs = gdf1.crs
    gdf2 = gdf2.to_crs(gdf1_crs)

    # Create a new GeoDataFrame to store the results
    result_gdf = gdf1.copy()

    """
        multiprocessing part
    """
    
    # Define the number of processes to use
    # num_processes = int(np.floor(multiprocessing.cpu_count() * 0.75)) if int(np.floor(multiprocessing.cpu_count() * 0.75)) > 1 else 1
    # num_processes = multiprocessing.cpu_count() // 2
    num_processes = 4
    
    # Create argument tuples for each row
    args = [(index, feature1, gdf2, spatial_index, gdf1_crs) for index, feature1 in gdf1.iterrows()]

    # Create a pool of worker processes
    with multiprocessing.Pool(processes=num_processes) as pool:
        try:
            # Apply the processing function to each row in parallel
            results = pool.map(check_the_data, args)
        except KeyboardInterrupt:
            if pool:
                pool.terminate()
    # Update the result GeoDataFrame
    for index, overlap_area in results:
        result_gdf.at[index, 'overlap_area'] = overlap_area

    return result_gdf

def filter(grid_gdf, threshold_percentage, id_field):
    merged_geometries = []
    # Filter and merge grids with overlap area more than threshold_percentage of the grid area
    for id_val in grid_gdf[id_field].unique():
        selected_grids = grid_gdf[(grid_gdf[id_field] == id_val) & (grid_gdf['overlap_area'] > grid_gdf['geometry'].area * threshold_percentage / 100)]
        if not selected_grids.empty:
            merged_geometry = unary_union(selected_grids['geometry'])
            merged_geometries.append(merged_geometry)

    # Create a new GeoDataFrame for the merged geometries
    merged_gdf = gpd.GeoDataFrame(geometry=merged_geometries, crs=grid_gdf.crs)

    return merged_gdf


def grid_selection(gdf1, gdf2, file_path):
    # Reproject gdf2 to match the CRS of gdf1
    gdf2 = gdf2.to_crs(crs=gdf1.crs)

    result_gdf = calculate_overlap_area_per_feature(gdf1, gdf2)

    # Set the threshold percentage for selecting grids (e.g., 25%)
    threshold_percentage = 50

    # Specify the ID field name for grids
    id_field = 'id'

    # Filter grids with overlap area more than 25% of the grid area
    return filter(result_gdf, threshold_percentage, id_field)

def save_to_file(merged_gdf, file_path, output_geojson):
    features = []
    count = 0
    for index, row in merged_gdf.iterrows():
        geom = row.geometry
        geom_json = geom.__geo_interface__
        
        # feature structure
        geojson = {
            'type':'Feature',
            'properties':{
                'id': count,
                'kelas':'bangunan'
            },
            'geometry': {
                'type': geom_json["type"],
                'coordinates': geom_json["coordinates"]
            }
        }
        features.append(geojson)
        count += 1

    feature_coll = {
        'type':'FeatureCollection',
        'name': output_geojson,
        'crs':{
            'type':'name',
            'properties':{
                'name':f'urn:ogc:def:crs:EPSG::{merged_gdf.crs.to_epsg()}'
            }
        },
        'features': features
    }

    with open(output_geojson, 'w') as f:
        f.write(json.dumps(feature_coll, indent=2))
