"""
Build 3D model of building with respective roofs.
The output will be in cityjson format.
Find more about cityjson in https://www.cityjson.org/
"""
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import fiona
import numpy as np
import rasterio
from tqdm.autonotebook import tqdm

from ._drape import DRAPE_MODE

CJSON_SCHEMA: Dict[str, Any] = {
    "type": "CityJSON",
    "version": "1.0",
    "metadata": {"referenceSystem": "", "geographicalExtent": []},
    "appearance": {
        "materials": [
            {
                "name": "roofandground",
                "ambientIntensity": 0.2000,
                "diffuseColor": [0.9000, 0.1000, 0.7500],
                "transparency": 0.0,
                "isSmooth": False,
            },
            {
                "name": "wall",
                "ambientIntensity": 0.4000,
                "diffuseColor": [0.1000, 0.1000, 0.9000],
                "transparency": 0.0,
                "isSmooth": False,
            },
        ]
    },
    "CityObjects": {},
    "vertices": [],
}

CJSON_SURFACE = (
    {"type": "RoofSurface"},
    {"type": "GroundSurface"},
    {"type": "WallSurface"},
)


@dataclass
class Py3dModelConfig:
    """A configuration for drape Shapefile to surface"""

    input_building: str
    input_surface: str
    output_file: Optional[str] = None
    input_roof: Optional[str] = None
    mode: str = "onedge"
    radius: Optional[float] = None
    input_dem: Optional[str] = None
    building_type: str = "MultiSurface"
    texture: Optional[Dict] = None


@dataclass
class BuildingConfigPerLayer:
    """A configuration to create building per layer"""

    vertices: List
    identifier: str
    building_geometry: List[List[List[float]]]
    surface: Dict[str, Union[np.ndarray, rasterio.Affine]]
    radius: float
    dem: Dict[str, Union[np.ndarray, rasterio.Affine]]
    mode: str


@dataclass
class BuildingSurface:
    """To save building surface data"""

    geometry: Union[List[List[List[int]]], List[List[List[List[int]]]]]
    semantic: List[int]
    material: List[int]


def create_model(config: Py3dModelConfig) -> Dict:
    """
    Create 3D building model from 2D polygon and Object Height Model (surface).

        Parameters:
            config (Py3dModelConfig) :
                input_building_shp (str) : building shp file location
                input_surface_tiff (str) : surface in tiff file location
                output_file (str) : where to save the file
                input_roof_shp (str) : roof shp file location
        Returns:
            cityjson_res (dict) : 3D model in cityjson
    """
    with rasterio.open(config.input_surface) as surface, fiona.open(
        config.input_building
    ) as buildings:

        # surface_epsg = str(surface.crs).split(":")[1]
        # buildings_epsg = buildings.crs["init"].split(":")[1]
        surface_epsg = surface.crs.to_epsg()
        buildings_epsg = buildings.crs.to_epsg()

        if surface_epsg != buildings_epsg:
            v_epsg = f"vector epsg:${buildings_epsg}"
            s_epsg = f"surface epsg:${surface_epsg}"
            error_msg = f"Different ref. system : {v_epsg} and {s_epsg}"
            raise ValueError(error_msg)

        surface_array = surface.read(1)
        surface_affine = surface.transform

        lod = 1 if config.input_roof is None else 2
        cityjson = CJSON_SCHEMA.copy()
        cityjson["metadata"][
            "referenceSystem"
        ] = f"urn:ogc:def:crs:EPSG::{buildings_epsg}"

        # drape and construct building surface
        building_vertex_count, vertices, cityjson = _create_buildings(
            cityjson, buildings, surface_array, surface_affine, lod, config
        )

        cityjson["vertices"] = vertices
        vertices_as_array = np.array(vertices)
        cityjson["metadata"]["geographicalExtent"] = [
            np.min(vertices_as_array[:, 0]),
            np.min(vertices_as_array[:, 1]),
            np.min(vertices_as_array[:, 2]),
            np.max(vertices_as_array[:, 0]),
            np.max(vertices_as_array[:, 1]),
            np.max(vertices_as_array[:, 2]),
        ]
        
        if config.output_file is not None:
            with open(config.output_file, "w") as outfile:
                json.dump(cityjson, outfile)
            print(f"saved as {config.output_file}")

        return cityjson


def _create_buildings(
    cityjson: Dict,
    buildings: fiona.collection,
    surface_array: np.ndarray,
    surface_affine: rasterio.Affine,
    lod: int,
    config: Py3dModelConfig,
    **args,
) -> Tuple[Dict, List, Dict]:
    """Create 3D Model per building"""
    dem_file: Optional[rasterio.DatasetReader] = None
    if config.input_dem is not None:
        dem_file = rasterio.open(config.input_dem)
        dem = {"array": dem_file.read(1), "affine": dem_file.transform}
    else:
        dem = {"array": None, "affine": None}

    vertices: List[List[float]] = []
    building_vertex_count: Dict[str, List[int]] = {}
    for building in tqdm(buildings, desc="Building"):
        (
            vertices,
            building_data,
            vertex_count,
            inner_wall,
        ) = _create_building_per_layer(
            BuildingConfigPerLayer(
                vertices=vertices,
                identifier=building["properties"]["uuid_bgn"],
                building_geometry=building["geometry"]["coordinates"],
                surface={"array": surface_array, "affine": surface_affine},
                radius=config.radius,
                dem=dem,
                mode=config.mode,
            )
        )
        building_vertex_count = {**building_vertex_count, **vertex_count}
        if config.building_type == "MultiSurface" and not inner_wall.geometry:
            pass

        elif config.building_type == "Solid" and not inner_wall.geometry:
            building_data.geometry = [building_data.geometry]
            building_data.material = [building_data.material]
            building_data.semantic = [building_data.semantic]

        elif config.building_type == "MultiSurface" and inner_wall.geometry:
            building_data.geometry += inner_wall.geometry
            building_data.semantic += inner_wall.semantic
            building_data.material += inner_wall.material

        elif config.building_type == "Solid" and inner_wall.geometry:
            building_data.geometry = [
                building_data.geometry,
                inner_wall.geometry,
            ]

            building_data.material = [
                building_data.material,
                inner_wall.material,
            ]

            building_data.semantic = [
                building_data.semantic,
                inner_wall.semantic,
            ]

        else:
            raise ValueError("Undefined or unsupported building type")

        
        cityjson["CityObjects"][building["properties"]["uuid_bgn"]] = {
            "type": "Building",
            "attributes": dict(building["properties"]),
            "geometry": [
                {
                    "type": config.building_type,
                    "boundaries": building_data.geometry,
                    "semantics": {
                        "values": building_data.semantic,
                        "surfaces": CJSON_SURFACE,
                    },
                    "material": {"": {"values": building_data.material}},
                    "lod": lod,
                }
            ],
        }

    if config.input_dem is not None:
        dem_file.close()

    return building_vertex_count, vertices, cityjson


def _get_building_coordinate(
    linear_ring: List[List[float]], config: BuildingConfigPerLayer
) -> Tuple[List[List[float]], List[List[float]]]:
    # create top vertices and bottom vertices
    building_top_coordinates = [
        DRAPE_MODE[config.mode](
            building_coordinate,
            config.surface["array"],
            config.surface["affine"],
            config.surface["affine"][0],
            config.radius,
        )
        for building_coordinate in linear_ring
    ]
    building_bottom_coordinates = [
        [building_coordinate[0], building_coordinate[1], 0]
        if config.dem["array"] is None
        else DRAPE_MODE[config.mode](
            building_coordinate,
            config.dem["array"],
            config.dem["affine"],
            config.dem["affine"][0],
            config.radius,
        )
        for building_coordinate in linear_ring
    ]

    # average of building height
    mean_building_top_z = np.average(np.array(building_top_coordinates)[:, 2])
    building_top_coordinates = [
        [xyz[0], xyz[1], mean_building_top_z] for xyz in building_top_coordinates
    ]

    if config.dem["array"] is not None:
        mean_building_bottom_z = np.average(np.array(building_bottom_coordinates)[:, 2])
        building_bottom_coordinates = [
            [xyz[0], xyz[1], mean_building_bottom_z]
            for xyz in building_bottom_coordinates
        ]

    return building_top_coordinates, building_bottom_coordinates


def _create_building_per_layer(
    config: BuildingConfigPerLayer,
) -> Tuple[List, BuildingSurface, Dict, BuildingSurface]:
    """Create Building per layer and add each linear ring without roof"""
    vertices = config.vertices
    building_vertex_count: Dict[str, List[int]] = {}
    building = BuildingSurface(geometry=[], semantic=[], material=[])
    wall = BuildingSurface(geometry=[], semantic=[], material=[])

    for i, linear_ring in enumerate(config.building_geometry):
        linear_ring = linear_ring[:-1]
        # create top vertices and bottom vertices

        (
            building_top_coordinates,
            building_bottom_coordinates,
        ) = _get_building_coordinate(linear_ring, config)

        vertices += building_top_coordinates
        vertices += building_bottom_coordinates

        # construct wall surface
        top_vertex = len(vertices) - (
            len(building_top_coordinates) + len(building_bottom_coordinates)
        )
        bottom_vertex = len(vertices) - len(building_bottom_coordinates)

        for j in range(len(building_top_coordinates)):
            last = False if j != len(building_top_coordinates) - 1 else True
            wall_surface = _construct_wall_surface(
                top_vertex, bottom_vertex, j, last=last
            )
            if i == 0:
                wall_surface.reverse()

            wall.semantic.append(2)
            wall.material.append(1)
            wall.geometry.append([wall_surface])

        # construct flat roof surface
        cityjson_top_geom = [
            top_vertex + j for j in range(len(building_top_coordinates))
        ]
        cityjson_top_geom.reverse()

        # construct ground surface
        cityjson_bottom_geom = [
            bottom_vertex + j for j in range(len(building_bottom_coordinates))
        ]

        if i == 0:
            building.geometry.append([cityjson_top_geom])
            building.geometry.append([cityjson_bottom_geom])

            building.semantic.append(0)
            building.material.append(0)

            building.semantic.append(1)
            building.material.append(0)

            building.geometry += wall.geometry
            building.semantic += wall.semantic
            building.material += wall.material

            # empty wall data to contain inner wall
            wall = BuildingSurface(geometry=[], semantic=[], material=[])
        else:
            building.geometry[0].append(cityjson_top_geom)
            building.geometry[1].append(cityjson_bottom_geom)

        building_vertex_count[config.identifier] = [
            top_vertex,
            top_vertex
            + len(building_top_coordinates)
            + len(building_bottom_coordinates),
        ]
    return vertices, building, building_vertex_count, wall

def _construct_wall_surface(
    top_vertex: int, bottom_vertex: int, addition: int, last: bool = False
) -> List[int]:
    if last is True:
        wall = [
            top_vertex + addition,
            top_vertex,
            bottom_vertex,
            bottom_vertex + addition,
        ]
    else:
        wall = [
            top_vertex + addition,
            top_vertex + addition + 1,
            bottom_vertex + addition + 1,
            bottom_vertex + addition,
        ]
    return wall
