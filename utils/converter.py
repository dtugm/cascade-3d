import json 
from osgeo import gdal
import numpy as np
    
def to_json(polygons, file_path, size):
    res = []
    count = 0

    for polygon in polygons:
        coords = polygon.exterior.coords
        divided_coords = [[x / size, y / size] for x, y in coords]

        res.append({
            'id': count,
            'hasil': divided_coords
        })

        count += 1

    encoded = json.dumps(res, cls=NumpyArrayEncoder, indent=2)

    with open(file_path, 'w') as f:
        f.write(encoded)

    return file_path

class NumpyArrayEncoder(json.JSONEncoder):
    # definisi encoder untuk membaca list sebagai json
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class Converter:
    def __init__(self, input_path:str, output_path:str, epsg:int, extent, dim):
        with open(input_path, 'r') as r:
            self.input = json.load(r)

        rangeX = extent[2] - extent[0]
        rangeY = extent[3] - extent[1]

        scaleX = 1 #(dim.dim[1] / (dim.w0))
        scaleY = 1 #(dim.dim[0] / (dim.h0))

        # Adjust the extent coordinates
        extent[2] = extent[0] + (rangeX * scaleX)
        extent[1] = extent[3] - (rangeY * scaleY)

        self.metadata = [rangeX, rangeY, scaleX, scaleY, extent[2], extent[1]]

        self.output = output_path
        self.epsg = epsg
        self.extent = extent


    def to_geojson(self):
        feature = []

        for data in self.input:
            if data['hasil'] == []:
                pass
            else:
                # transformasi
                for i in range(len(data['hasil'])):
                    data['hasil'][i][1] *= (-1)
                    data['hasil'][i][1] += 1
                    for j in [0,1]:
                        data['hasil'][i][j] *= (self.extent[j+2] - self.extent[j])
                        data['hasil'][i][j] += self.extent[j]

                # struktur feature
                geojson = {
                    'type':'Feature',
                    'properties':{
                        'id':data['id'],
                        'kelas':'bangunan'
                    },
                    'geometry':{
                        'type':'Polygon',
                        'coordinates':[data['hasil']]
                    }
                }

                feature.append(geojson)

        feature_coll = {
            'type':'FeatureCollection',
            'name':self.output,
            'crs':{
                'type':'name',
                'properties':{
                    'name':f'urn:ogc:def:crs:EPSG::{self.epsg}'
                }
            },
            'features':feature
        }
        
        with open(self.output, 'w') as f:
            f.write(json.dumps(feature_coll, indent=2))

        return self.output