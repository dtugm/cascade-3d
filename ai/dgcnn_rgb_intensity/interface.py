from dataclasses import dataclass
from typing import Optional

@dataclass
class DGCNNParams:
    #batch size in testing [default: 32]
    batch_size: int = 16    
    #specify gpu device
    gpu: str = '0'          
    # point number [default: 4096]
    num_point: int = 4096
    # experiment root (required)
    log_dir: str = ""
    # visualize result [default: False] (action = store_true)
    visual: bool = False
    # area for testing, option: 1-6 [default: 5]
    test_area: Optional[int] = None
    # aggregate segmentation scores with voting [default: 5]
    num_votes: int = 5
    # How many classes used for segmentation [default: 9]
    num_classes: int = 3
    # dropout rate
    dropout: float = 0.5
    # Dimension of embeddings (metavar='N')
    emb_dims: int = 1024
    # Num of nearest neighbors to use (metavar='N')
    k: int = 20
    # Name of point cloud data (required)
    point_cloud: str = ""
    # Size of each block
    block_size: int = 1000
    # model directory
    model: str = ""
    # output directory
    output_path: str = ""