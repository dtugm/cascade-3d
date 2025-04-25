from shapely.geometry import Polygon, MultiPolygon
import geopandas
from osgeo import gdal

class GeojsonProcessing:
    def __init__(self, gdf: geopandas.GeoDataFrame, output_path:str, image_shape, epsg:int, extent):
        self.input = gdf
        self.img_width, self.img_height = image_shape

        rangeX = extent[2] - extent[0]
        rangeY = extent[3] - extent[1]

        self.scaleX = self.img_width / (extent[2] - extent[0])
        self.scaleY = self.img_height / (extent[3] - extent[1])

        # Adjust the extent coordinates
        extent[2] = extent[0] + (rangeX * 1)#self.scaleX)
        extent[1] = extent[3] - (rangeY * 1)#self.scaleY)

        self.metadata = [rangeX, rangeY, self.scaleX, self.scaleY, extent[2], extent[1]]

        self.output = output_path
        self.epsg = epsg
        self.extent = extent

    def calculate_reduces_coordinates_values(self, coords):
        for i in range(len(coords)):
            coord = list(coords[i])
            
            coord[0] = (coord[0] - self.extent[0]) * self.scaleX
            coord[1] = (coord[1] - self.extent[1]) * self.scaleY

            coord[1] -= self.metadata[1] * self.scaleY
            coord[1] *= (-1) 

            coords[i] = (coord[0], coord[1])
        return Polygon(coords)
    
    def reduce_coordinates_values(self):
        for index, feature in self.input.iterrows():
            geometry = feature.geometry
            
            if geometry.geom_type == "Polygon":
                polygon = self.calculate_reduces_coordinates_values(list(geometry.exterior.coords))
                self.input.loc[index, "geometry"] = polygon

            elif geometry.geom_type == "MultiPolygon":
                polygons = []
                for polygon in geometry.geoms:
                    polygon = self.calculate_reduces_coordinates_values(list(polygon.exterior.coords))
                    polygons.append(polygon)
                self.input.loc[index, "geometry"] = MultiPolygon(polygons)

        return self.input
    
    def calculate_revert_coordinates_value(self, coords):
        for i in range(len(coords)):
            coord = list(coords[i])
            
            coord[1] *= (-1)
            coord[1] += self.metadata[1] * self.scaleY

            coord[1] = (coord[1] / self.scaleY) + self.extent[1]
            coord[0] = (coord[0] / self.scaleX) + self.extent[0]

            coords[i] = (coord[0], coord[1])
        return Polygon(coords)
    
    def revert_coordinates_values(self, gdf):
        for index, feature in gdf.iterrows():
            geometry = feature.geometry

            if geometry.geom_type == "Polygon":
                polygon = self.calculate_revert_coordinates_value(list(geometry.exterior.coords))
                gdf.loc[index, "geometry"] = polygon

            elif geometry.geom_type == "MultiPolygon":
                polygons = []
                for polygon in geometry.geoms:
                    polygon = self.calculate_revert_coordinates_value(list(polygon.exterior.coords))
                    polygons.append(polygon)
                gdf.loc[index, "geometry"] = MultiPolygon(polygons)
        
        return gdf

    def save_to_file(self, gdf, filename=""):
        filename = filename if filename else self.output
        
        try:
            gdf.to_file(filename)
        except Exception as e:
            raise e
