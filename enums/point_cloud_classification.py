from enum import Enum

class AlgorithmOptions(Enum):
    RF = "Machine Learning - Random Forest (CPU Only)"
    XG_BOOST = "Machine Learning - XGBoost"
    DGCNN = "Deep Learning"

class FeatureOptions(Enum):
    RGB = "XYZ RGB"
    INTENSITY = "XYZ Intensity"