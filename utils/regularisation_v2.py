import numpy as np
import time
import math
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import Point
import shapely
from shapely.geometry import Point, Polygon

def get_angles_and_coords(gdf):
    geom = gdf.iloc[0].geometry        
    # boundary = geom.boundary
    # coords = [c for c in boundary.coords]
    # time.sleep(1)

    mbr = geom.minimum_rotated_rectangle
    coords = list(mbr.exterior.coords)

    segments = [shapely.geometry.LineString([a, b]) for a, b in zip(coords,coords[1:])]
    longest_segment = max(segments, key=lambda x: x.length)
    p1, p2 = [c for c in longest_segment.coords]
    anglest = math.degrees(math.atan2(p2[1]-p1[1], p2[0]-p1[0])) #https://stackoverflow.com/questions/42258637/how-to-know-the-angle-between-two-points

    return anglest, coords

def calculate_dimension(coords):
    edge_length=(Point(coords[0]).distance(Point(coords[1])),Point(coords[1]).distance(Point(coords[2])))
    length = max(edge_length)
    width = min(edge_length)

    return length, width
# length, width = calculate_dimension(coords)

def create_grids(gdf, grid_size=1300):
    xmin, ymin, xmax, ymax=gdf.total_bounds

    cols = list(range(int(np.floor(xmin)), int(np.ceil(xmax)), grid_size))
    rows = list(range(int(np.floor(ymin)), int(np.ceil(ymax)), grid_size))
    rows.reverse()
    polygons = []

    for x in cols:
        for y in rows:
            polygons.append( Polygon([(x,y), (x+grid_size, y), (x+grid_size, y+grid_size), (x, y+grid_size)]) )
    # grids = gpd.GeoDataFrame({'geometry':polygons}, crs = gdf.crs.to_string())
    grids = gpd.GeoDataFrame({'geometry': polygons})

    grids['CASE'] = "FILLED"

    return grids

def filter_grids_based_on_actual_geometry(grids, polygon, overlap_threshold=0.5):
    for index, grid in grids.iterrows():
        intersection: Polygon = grid.geometry.intersection(polygon)
        if not intersection.is_empty and intersection.area > grid.geometry.area * overlap_threshold:
            continue
        else:
            grids.loc[index, "CASE"] = "EMPTY"

    filtered_grid=grids[grids['CASE'].str.contains("FILLED")]
    filtered_grid=filtered_grid.reset_index(drop=True)

    return filtered_grid

def filter_grids_based_on_rotated_geometry(grids, gdf: gpd.GeoDataFrame):
    df4_merged_geom = gdf.unary_union

    for index, polygon in grids.iterrows():
        if polygon.geometry.disjoint(df4_merged_geom):
            grids.loc[index, "CASE"] = "EMPTY"

    filtered_grid=grids[grids['CASE'].str.contains("FILLED")]
    filtered_grid=filtered_grid.reset_index(drop=True)
    
    return filtered_grid

def rotate_gdf(data, angles):
    return data.rotate(angles, origin=data.centroid.item())

def to_gdf(geoms, case=False):
    gdf = gpd.GeoDataFrame({ 'geometry': geoms })

    if case:
        gdf['CASE'] = 'FILLED'
    
    return gdf



# essias=Polygon([[32250, 175889], [33913, 180757], [29909, 182124], [28246, 177257], [32250, 175889]])
# d = {'geometry': [Polygon([(32250, 175889), (30913, 170757), (29909, 182124), (20246, 177257), (32250, 175889)])]}
# d = {'geometry': [Polygon([(30000, 170000), (35913, 175757), (29909, 182124), (24000, 175757), (30000, 170000)])]}
# gdf = gpd.GeoDataFrame(d, crs="EPSG:4326")

# polygon = Polygon([(32250, 175889), (40913, 170757), (29909, 182124), (20246, 177257), (32250, 175889)])
# gdf = to_gdf([polygon]) # gpd.GeoDataFrame({ 'geometry': [polygon] })
"""

anglest, coords = get_angles_and_coords(gdf)
rotated_gdf = rotate_gdf(gdf, -anglest)

rotated_grids = create_grids(rotated_gdf)
filtered_grids = filter_grids_based_on_rotated_geometry(rotated_grids, rotated_gdf)


# rotate gdf back
grids = filtered_grids.rotate(anglest, origin=gdf.centroid.item()) #
# Convert to GeoDataFrame using a dictionary
grids = to_gdf(grids, case=True)

filtered_grids = filter_grids_based_on_actual_geometry(grids, polygon)

union_geometry = filtered_grids.unary_union
res_gdf = gpd.GeoDataFrame({ 'geometry': [union_geometry] })

# gdf_loc_apres = res_gdf.iloc[1] 
grids.to_file("files/gdf grids.shp")
res_gdf.to_file("files/gdf grid_comple.shp")
gdf.to_file("files/gdf original.shp")
rotated_gdf.to_file("files/gdf rotated.shp")

"""
