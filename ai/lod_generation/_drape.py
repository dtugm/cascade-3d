"""
Drape from vector to surface
"""
from math import sqrt
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
from rasterio import Affine


def _calc_row_col(x: float, y: float, affine: Affine) -> Tuple[int, int]:
    col, row = ~affine * (x, y)
    return int(col), int(row)


def todsm(
    coord: List[float], dsm_array: np.ndarray, affine: Affine, *args
) -> Tuple[float, float, float]:
    """drape to dsm

    Arguments:
        coord {[type]} -- [description]
        dsm_array {[type]} -- [description]
        affine {[type]} -- [description]

    Raises:
        ValueError: [description]

    Returns:
        [type] -- [description]
    """
    # if len(coord) > 3:
    #     print(coord)
    #     raise ValueError("Don't use multi type geometry")

    x, y = coord[0], coord[1]
    col, row = _calc_row_col(x, y, affine)
    draped_z = dsm_array[row, col].astype(np.float64)
    return (x, y, draped_z) if draped_z > -32767 else (x, y, 0.0)


def todsm_onedge(
    coord: List[float],
    dsm_array: np.ndarray,
    affine: Affine,
    res_sp: float,
    radius: float = None,
) -> Tuple[float, float, float]:
    """Drape to building edges

    Arguments:
        coord {[type]} -- [description]
        dsm_array {[type]} -- [description]
        affine {[type]} -- [description]
        res_sp {[type]} -- [description]

    Keyword Arguments:
        radius {[type]} -- [description] (default: {None})

    Raises:
        ValueError: [description]
        ValueError: [description]

    Returns:
        [type] -- [description]
    """
    # if len(coord) > 3:
    #     print(coord)
    #     raise ValueError("Don't use multi type geometry")

    x, y = coord[0], coord[1]
    kernel_size = int((radius / res_sp) * 2) if radius is not None else 9
    if radius is not None and kernel_size <= 1:
        raise ValueError(
            f"Radius of ${radius} must be 3 times than ${res_sp} of spatial resolution"
        )
    mid = (kernel_size - 1) // 2
    col, row = _calc_row_col(x, y, affine)
    kernel = dsm_array[row - mid : row + mid + 1, col - mid : col + mid + 1]

    return (x, y, np.max(kernel))

DRAPE_MODE: Dict[str, Callable[[Any], Tuple[float, float, float]]] = {
    "normal": todsm,
    "onedge": todsm_onedge,
}
