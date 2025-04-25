from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import numpy as np
import rasterio

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