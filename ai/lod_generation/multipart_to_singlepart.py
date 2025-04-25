
import geopandas as gpd

def multipart_to_singlepart(input_file, output_file):
    # Read input file
    gdf = gpd.read_file(input_file)

    # Drop the existing 'level_1' column if it exists
    if 'level_1' in gdf.columns:
        # gdf.set_index('level_1', inplace=True)
        gdf = gdf.drop(columns=['level_1'])
    if 'level_0' in gdf.columns:
        # gdf.set_index('level_0', inplace=True)
        gdf = gdf.drop(columns=['level_0'])

    # Convert multipart to singlepart
    singlepart_gdf = gdf.explode(index_parts=True)

    # Save the result to output file
    singlepart_gdf.to_file(output_file)

    print("Singlepart file created successfully:", output_file)