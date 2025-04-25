import geopandas as gpd
from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly

class Meta:
    def __init__(self, path:str):
        self.path = path
        extension = path.split(".")[-1]

        if extension == "tif":
            self.data = gdal.Open(self.path, GA_ReadOnly)
        elif extension == "geojson":
            self.gdf: gpd.GeoDataFrame = gpd.read_file(path)
    
    """
        Geojson File
    """
    def get_extent(self):
        extent = self.gdf.bounds
        
        minx = min(extent.minx)
        miny = min(extent.miny)
        maxx = max(extent.maxx)
        maxy = max(extent.maxy)
        ext = [minx, miny, maxx, maxy]

        return ext
    
    def get_epsg(self):
        crs = self.gdf.crs
        epsg = crs.srs
        epsg_code = int(epsg.split(":")[1])
        
        return epsg_code
    
    """
        Raster File (tif)
    """
    def get_extent_from_raster(self):
        geoTransform = self.data.GetGeoTransform()
        minx = geoTransform[0]
        maxy = geoTransform[3]
        maxx = minx + geoTransform[1] * self.data.RasterXSize
        miny = maxy + geoTransform[5] * self.data.RasterYSize
        ext = [minx, miny, maxx, maxy]
        # data = None

        return ext
    
    def get_epsg_from_raster(self):
        if self.data is None:
            print(f"Error: Unable to open raster file {self.path}")
            return None

        # Get the raster's spatial reference
        spatial_ref = self.data.GetProjection()

        # Create a spatial reference object
        srs = osr.SpatialReference()
        srs.ImportFromWkt(spatial_ref)

        # Get the EPSG code
        epsg_code = srs.GetAttrValue('AUTHORITY', 1)

        dataset = None  # Close the dataset

        return epsg_code
    