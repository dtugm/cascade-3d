import laspy
import numpy as np

def read_las(filepath, isIntensity = False):
    inFile = laspy.read(filepath)
    x = inFile.x
    y = inFile.y
    z = inFile.z

    if isIntensity:
        I = inFile.intensity
        data = np.column_stack((x, y, z, I))
    else:
        r = inFile.red
        g = inFile.green
        b = inFile.blue
        data = np.column_stack((x, y, z, r, g, b))
    
    return data

def save_las(data, output_path: str, isIntensity: bool = False):
    ext = "laz" if isIntensity else "las"

    header = laspy.LasHeader(point_format=2, version="1.2")
    las = laspy.LasData(header)
    las.x = data[:, 0]
    las.y = data[:, 1]
    las.z = data[:, 2]

    # Class: 2 = ground, 5 = vegetation, 6 = building
    reverse_mapping = {0: 2, 1: 5, 2: 6}
    if isIntensity:
        las.intensity = data[:, 3]
        classification_data = np.array([reverse_mapping[label] for label in data[:, 4]])
    else:
        las.red = data[:, 3]
        las.green = data[:, 4]
        las.blue = data[:, 5]
        classification_data = np.array([reverse_mapping[label] for label in data[:, 6]])
    
    classification_data = classification_data.astype(np.uint8)
    las.classification = classification_data

    las.write(f"{output_path}.{ext}")