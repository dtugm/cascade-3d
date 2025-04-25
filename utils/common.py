import datetime
import os
import sys
from osgeo import gdal

def raster_to_png(file_path: str):
    output_path = file_path.replace('.tif', '.png')
    gdal.Translate(output_path, file_path, format='PNG')

    return output_path

def resource_path(relative_path: str = ""):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_file_extension(filepath: str = ""):
    splitted = filepath.split(".")
    
    return splitted[len(splitted)-1]

def get_current_time():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def get_current_time_for_filename():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y%m%d%H%M%S")
    return formatted_time

def get_base_dir():
    return os.path.dirname(os.path.abspath(os.getcwd()))

def get_temp_dir():
    return os.path.join(get_root_dir(), "temp")

def get_root_dir():
    return os.getcwd()

def get_filename_from_filepath(filepath: str):
    filename = os.path.basename(filepath)
    filename = os.path.splitext(filename)[0]
    return filename

def set_output_path(input_path, output_path, ext, is_include_timestamp=False):
    filename = get_filename_from_filepath(input_path)
    if is_include_timestamp:
        filename = f"{filename}_{get_current_time_for_filename()}"

    output = os.path.join(output_path, f"{filename}.{ext}")
    
    os.makedirs(output_path, exist_ok=True)
    
    return output

def set_text_with_color(text, color="black"):
    return f'<span style="color:{color};">{text}</span>'

waiting_spinner_commands = ["Load file", "Start regularisation", "Success", "Regularisation finished"]

outline_stylesheet = "border: 0.5px solid gray; border-radius: 5px;"
outline_stylesheet_transparent = "border: 1px solid transparent; border-radius: 5px;"

accepted_extension = ["tif", "geojson"]