import geopandas as gpd
import pandas as pd
import numpy as np
import multiprocessing
import json

from shapely.geometry import Polygon, GeometryCollection
from shapely.ops import unary_union
from shapely import Geometry, geometry

def create_mbr(polygon: Polygon):
    """
        create MBR
    """
    return polygon.minimum_rotated_rectangle

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

def generate_grid(mbr_polygon, grid_size):
    # # Get the polygon's exterior ring coordinates
    # exterior_coords = mbr_polygon.exterior.coords

    # # Calculate the rectangle's width and height based on the first and last coordinates
    # width = abs(exterior_coords[0][0] - exterior_coords[-1][0])
    # height = abs(exterior_coords[0][1] - exterior_coords[-1][1])

    # # Determine the grid orientation based on rectangle dimensions
    # if width > height:  # Wider rectangle, horizontal grid lines
    #     x_step = grid_size
    #     y_step = 0
    # else:  # Taller rectangle, vertical grid lines
    #     x_step = 0
    #     y_step = grid_size

    # # Get the minimum coordinates (assuming rectangle doesn't have holes)
    # xmin = min(coord[0] for coord in exterior_coords)
    # ymin = min(coord[1] for coord in exterior_coords)

    # # Create a list to store the grids
    # grids = []

    # # Loop through grid positions based on rectangle dimensions
    # for y in np.arange(ymin, ymin + height + y_step, y_step):
    #     for x in np.arange(xmin, xmin + width + x_step, x_step):
    #         # Create the grid cell polygon with adjusted coordinates
    #         grid_polygon = Polygon([(x, y), (x + grid_size, y), 
    #                                 (x + grid_size, y + grid_size), (x, y + grid_size)])
    #         if grid_polygon.intersects(mbr_polygon):
    #             intersection: Polygon = grid_polygon.intersection(mbr_polygon)
    #             if not intersection.is_empty:
    #                 # grid_data_list.append(intersection)
    #                 grids.append(grid_polygon)
    # return grids
    
    grid_data_list = []

    # Read coordinates
    coordinates_list = list(mbr_polygon.exterior.coords)

    # Calculate rotation angle
    rotation_angle = calculate_angles(coordinates_list)
    if rotation_angle[0] >= 50 or rotation_angle[0] <= -50:
        rotation_angle = rotation_angle[1]
    else:
        rotation_angle = rotation_angle[0]

    # Define cols based on grid size and bounding box
    xmin, ymin, xmax, ymax = mbr_polygon.bounds
    cols = int(np.ceil((xmax - xmin) / grid_size))
    rows = int(np.ceil((ymax - ymin) / grid_size))

    for i in range(cols):
        for j in range(rows):
            left = xmin + i * grid_size
            right = xmin + (i + 1) * grid_size
            bottom = ymin + j * grid_size
            top = ymin + (j + 1) * grid_size

            grid_polygon = Polygon([(left, bottom), (right, bottom), (right, top), (left, top)])
            if grid_polygon.intersects(mbr_polygon):
                intersection: Polygon = grid_polygon.intersection(mbr_polygon)
                if not intersection.is_empty:
                    # grid_data_list.append(intersection)
                    grid_data_list.append(grid_polygon)

    return grid_data_list


def grid_selection(grid_list: list[Polygon], polygon: Polygon, overlap_threshold=0.5):
    selected_grids = []
    for grid in grid_list:
        intersection: Polygon = grid.intersection(polygon)
        if not intersection.is_empty and intersection.area > grid.area * overlap_threshold:
            selected_grids.append(grid)

    # if not len(selected_grids):
    #     return
    
    merged_grids = unary_union(selected_grids)
    
    largest_geometry = None
    if merged_grids.geom_type == "GeometryCollection":
        largest_area = 0
        for geometry in merged_grids.geoms:
            if isinstance(geometry, Polygon):  # Check if Polygon (can modify for other types)
                current_area = geometry.area
                if current_area > largest_area:
                    largest_area = current_area
                    largest_geometry = geometry

    if largest_geometry is not None:
        return largest_geometry
    else:
        return merged_grids