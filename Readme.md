# Cascade 3D
## Description
CASCADE-3D (CAdastre and Spatial map adjustment with spatial Computation for Automatic builDing dEtection and 3D generation) is a graphical user interface (GUI) designed to support fast and accurate generation of geospatial data and three-dimensional (3D) building properties for multipurpose land management applications. The system focuses on the automated reconstruction of 3D building models at Levels of Detail (LOD) 1 and 2 using integrated photogrammetric processing and deep-learning-based spatial analysis.

CASCADE-3D integrates advanced deep-learning frameworks, including the Segment Anything Model (SAM) and Dynamic Graph Convolutional Neural Network (DGCNN), to automate building outline detection and point cloud classification. Photogrammetric processing based on Structure-from-Motion (SfM) and Multi-View Stereo (MVS) techniques is first applied to generate dense point clouds, true orthophotos, and Building Height Models (BHMs) from unmanned aerial vehicle (UAV) imagery. Building outlines are then extracted using SAM, a promptable segmentation model capable of zero-shot generalization without additional training.

The CASCADE-3D GUI provides tools for interactive digitization, automatic regularization, and refinement of building outlines based on their primary orientation. Building heights are derived from BHMs generated through point cloud classification using DGCNN, enabling the separation of ground and building classes from digital terrain models (DTMs). These outputs are subsequently used to reconstruct 3D building models at both LOD1 and LOD2.

For LOD2 reconstruction, CASCADE-3D emphasizes accurate roof structure extraction by analyzing roof orientation and geometric configuration. Roof detection techniques based on building aspect are applied to capture complex architectural forms. The system was evaluated using point clouds and orthophotos from 1,215 buildings across multiple provinces in Indonesia, representing diverse architectural patterns and land cover types. The results demonstrate CASCADE-3D’s capability in building outline detection, roof structure extraction, and automated LOD1 and LOD2 3D building reconstruction.

## Device & System Requirements
### Hardware

- **GPU**: NVIDIA GPU with CUDA support

- **Recommended**: Compute Capability ≥ 6.1

- **RAM**: Minimum 8 GB (16 GB recommended)

- **Storage**: ≥ 10 GB free disk space


### Software

- **Operating System**: Windows 10 / 11 (64-bit)

- **Python**: Python 3.9

- **NVIDIA Driver**: Compatible with CUDA 11.8

- **Git**: Required for git-based dependencies


### CUDA Requirement

This project uses CUDA-enabled PyTorch.

#### Verify CUDA support
```bash
nvidia-smi
```

You do not need to manually install the full CUDA Toolkit.
PyTorch CUDA wheels already bundle the required runtime libraries.

## Project Structure
```bash
cascade-3d/
├─ ai/
│  ├─ cityjson_viewer
│  ├─ dgcnn_rgb
│  ├─ dgcnn_rgb_intensity
│  ├─ digitasi_interaktif
│  ├─ lod_generation
│  ├─ point_cloud_classification
│  ├─ refine_rs_bo
│  └─ roof_footprint
├─ enums/
├─ lib/
│  └─ GDAL-3.4.3-cp39-cp39-win_amd64.whl
├─ public/
│  └─ icon/
├─ ui/
│  ├─ components/
│  ├─ lod1_tab.py
│  ├─ sam_interactive_tab.py
│  └─ ...
├─ utils/
├─ data/
├─ requirements.txt
├─ main.py
└─ README.md
```

## Sample Data

Sample datasets are located in the data/ directory.

- Used for testing and demonstration

- You may replace or add your own datasets here

- No additional configuration is required


## SAM Model Setup

This application requires a Segment Anything Model (SAM) checkpoint.

### Download
```bash
https://huggingface.co/spaces/abhishek/StableSAM/blob/main/sam_vit_h_4b8939.pth
```

### Placement
```bash
ai/sam/model/sam_vit_h_4b8939.pth
```

Make sure the file path matches exactly.

## Virtual Environment Setup

Create a virtual environment in the project root:

```bash
python -m venv venv
```

Activate the environment:

```bash
.\venv\Scripts\activate
```
## PowerShell Execution Policy Issue

If you encounter:
```bash
Activate.ps1 cannot be loaded because running scripts is disabled
```

Run once:
```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the virtual environment again.

## Dependencies Installation

All dependencies are managed via requirements.txt, including:

- CUDA-enabled PyTorch (CUDA 11.8)

- Local GDAL wheel

- Geospatial and ML libraries


From the project root:

```bash
pip install -r requirements.txt
```

Local GDAL Wheel

GDAL is installed from a relative local wheel located in:

```bash
lib/GDAL-3.4.3-cp39-cp39-win_amd64.whl
```

This ensures portability for other users using Python 3.9 on Windows.

Verify Installation (Optional)
```bash
python - <<EOF
import torch
from osgeo import gdal

print("CUDA available:", torch.cuda.is_available())
print("GDAL version:", gdal.VersionInfo())
EOF
```

Expected:

CUDA available: True

GDAL version 3040300 (or similar)

## Running the Application

1. Open a terminal in the project root

2. Activate the virtual environment

3. Run the application:

```bash
python main.py
```

## Troubleshooting
### GDAL Installation Fails

- Ensure Python version is 3.9

- Ensure the wheel filename matches cp39

- Do not install gdal from PyPI

### CUDA Not Detected

- Update NVIDIA driver

- Verify with nvidia-smi

### DLL or Import Errors

- Make sure all installs were done inside the virtual environment

- Avoid mixing global Python packages

- Developer Notes

- CUDA version: 11.8

- Python version is strictly pinned to 3.9

- GDAL is installed from a local wheel for stability

- Suitable for PyInstaller packaging (with additional hooks)

## Video Tutorials
The following video tutorials provide step-by-step guidance for using each feature in CASCADE-3D.
Each video demonstrates the workflow, required inputs, and expected outputs.

```
https://www.youtube.com
```