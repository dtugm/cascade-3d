from dataclasses import dataclass
from typing import Optional
from enums.point_cloud_classification import AlgorithmOptions, FeatureOptions

@dataclass
class PointCloudClassificationParams:
  algorithm: AlgorithmOptions = ""
  features: FeatureOptions = ""
  model: str = ""
  point_cloud_path: str = ""
  output_path: str = ""