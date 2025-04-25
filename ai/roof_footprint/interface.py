from dataclasses import dataclass
from typing import Optional

@dataclass
class RoofFootprintParams:
    ohm_path: str
    bo_path: str
    output_file: Optional[str] = None