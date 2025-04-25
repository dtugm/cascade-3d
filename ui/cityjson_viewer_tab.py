from PyQt5 import QtWidgets, QtCore
from enums.layout_type import LayoutType
from enums.file_extension import FileExtension
from enums.message_box_type import MessageBoxTypeEnum

from ui.components.input_file import FileInputComponent
from ui.components.button import Button
from ui.components.message_box import CustomMessageBox

from ai.cityjson_viewer.cityjson_to_obj import Cityjson2Obj
from ai.cityjson_viewer.interface import Cityjson2ObjParams

from utils.common import get_root_dir, get_current_time_for_filename

import os
import vtk
import json

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class CityjsonViewerTabWidget(QtWidgets.QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent)

        self.set_layout(type)

        # input
        self.cityjson = FileInputComponent(
            "Load CityJson",
            button_font_color="white",
            ext=[FileExtension.Json.value]
        )
        self.layout.addWidget(self.cityjson)

        # button
        self.button = Button("Process")
        self.button.clicked.connect(self.on_button_clicked)
        self.layout.addWidget(self.button)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # main layout
        self.main_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.main_layout)

        # left panel
        self.left_panel = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.left_panel, stretch=1)  

        # building id lists
        self.file_list = QtWidgets.QListWidget()
        self.file_list.clicked.connect(self.on_file_selected)
        self.left_panel.addWidget(self.file_list)

        self.create_table()
        self.left_panel.addWidget(self.attribute_table)

        self.reset_button = Button("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        self.left_panel.addWidget(self.reset_button)

        # right panel
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.main_layout.addWidget(self.vtk_widget, stretch=4)  

        # 3d Viewer
        self.renderer = vtk.vtkRenderer()
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        self.interactor = self.vtk_widget
        self.interactor.SetRenderWindow(self.render_window)

        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        self.models = {}
        self.current_actor = None
        self.cityjson_data = None

        self.add_axes()

        self.interactor.Initialize()
        self.interactor.Start()

    def create_table(self):
        self.attribute_table = QtWidgets.QTableWidget()
        self.attribute_table.setRowCount(4)
        self.attribute_table.setColumnCount(2)
        self.attribute_table.setMaximumHeight(165)

        #Table will fit the screen horizontally 
        self.attribute_table.horizontalHeader().setStretchLastSection(True) 
        self.attribute_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch) 

        self.attribute_table.setItem(0,0, QtWidgets.QTableWidgetItem("Level 0"))
        self.attribute_table.setItem(1,0, QtWidgets.QTableWidgetItem("Level 1"))
        self.attribute_table.setItem(2,0, QtWidgets.QTableWidgetItem("ID"))
        self.attribute_table.setItem(3,0, QtWidgets.QTableWidgetItem("UUID_BGN"))

    def set_table_value(self, filename):
        if not self.cityjson_data:
            return

        city_objects = self.cityjson_data.get("CityObjects", {})
        attributes = city_objects.get(filename, {}).get("attributes", {})

        keys_to_check = ["level_0", "level_1", "Id", "uuid_bgn"]
        if any(key not in attributes for key in keys_to_check):
            message_box = CustomMessageBox(
                "Warning",
                "One of the attributes was not found",
                parent=self,
                icon=MessageBoxTypeEnum.Warning.value
            )
            message_box.show()
            return
        
        self.attribute_table.setItem(0,1, QtWidgets.QTableWidgetItem(str(attributes["level_0"])))
        self.attribute_table.setItem(1,1, QtWidgets.QTableWidgetItem(str(attributes["level_1"])))
        self.attribute_table.setItem(2,1, QtWidgets.QTableWidgetItem(str(attributes["Id"])))
        self.attribute_table.setItem(3,1, QtWidgets.QTableWidgetItem(attributes["uuid_bgn"]))

    def set_layout(self, type=LayoutType.horizontal.value):
        if type == LayoutType.horizontal.value:
            self.layout = QtWidgets.QHBoxLayout(self)
        else:
            self.layout = QtWidgets.QVBoxLayout(self)

        self.setLayout(self.layout)
    
    def reset_all_data(self):
        self.models = {}
        self.current_actor = None
        self.cityjson_data = None
        
        # remove builidng id lists
        self.file_list.clear()
        # Remove value from attribute table
        self.attribute_table.setItem(0,1, QtWidgets.QTableWidgetItem(""))
        self.attribute_table.setItem(1,1, QtWidgets.QTableWidgetItem(""))
        self.attribute_table.setItem(2,1, QtWidgets.QTableWidgetItem(""))
        self.attribute_table.setItem(3,1, QtWidgets.QTableWidgetItem(""))
        # clear the vtk scene
        self.renderer.RemoveAllViewProps()
        self.renderer.GetRenderWindow().Render()

    def on_button_clicked(self):
        self.reset_all_data()

        self.temp_dir = os.path.join(get_root_dir(), "temp", get_current_time_for_filename())
        params = Cityjson2ObjParams(
            temp_dir=self.temp_dir,
            cityjson_path=self.cityjson.filename
        )
        print(self.temp_dir)

        # thread object
        self.qthread = QtCore.QThread()
        # worker object
        self.worker = Cityjson2Obj(params)
        # worker to thread
        self.worker.moveToThread(self.qthread)
        # connect signals and slots
        self.qthread.started.connect(self.worker.run)
        self.worker.progress.connect(self.handle_process_running)
        self.worker.finished.connect(self.handle_process_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.qthread.quit)
        self.worker.error.connect(self.handle_process_error)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.error.connect(self.qthread.quit)
        self.qthread.finished.connect(self.qthread.deleteLater)
        # start thread
        self.qthread.start()
        self.button.setEnabled(False)
        self.qthread.finished.connect(lambda: self.button.setEnabled(True))

    def handle_process_error(self, msg):
        self.progress_bar.setValue(100)
        message_box = CustomMessageBox(
            "Warning",
            f"Error : {msg}",
            parent=self,
            icon=MessageBoxTypeEnum.Critical.value
        )
        message_box.show()

    def handle_process_running(self, progres):
        self.progress_bar.setValue(int(progres))

    def handle_process_finished(self):
        print("ready to consume")

        self.load_cityjson(self.cityjson.filename)
        self.load_models(self.temp_dir)

    def load_cityjson(self, cityjson_file):
        with open(cityjson_file, 'r') as f:
            self.cityjson_data = json.load(f)

    def load_models(self, folder):
        files = os.listdir(folder)
        for index, file_name in enumerate(files):
            if file_name.endswith(".obj"):
                file_path = os.path.join(folder, file_name)
                file_name_without_extension = os.path.splitext(file_name)[0]
                self.file_list.addItem(file_name_without_extension)

                reader = vtk.vtkOBJReader()
                reader.SetFileName(file_path)
                reader.Update()

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(reader.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)

                self.models[file_name_without_extension] = actor
                self.renderer.AddActor(actor)

            progress = 80 + int((index+1)/len(files)*20)
            self.progress_bar.setValue(progress)    

        self.reset_view()

    def reset_view(self):
        self.renderer.GetActiveCamera().SetPosition(0, 0, 1)
        self.renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.renderer.GetActiveCamera().SetViewUp(0, 1, 0)  
        self.renderer.ResetCamera()
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def add_axes(self):
        axes = vtk.vtkAxesActor()
        orientation_marker = vtk.vtkOrientationMarkerWidget()
        orientation_marker.SetOrientationMarker(axes)
        orientation_marker.SetInteractor(self.interactor)
        orientation_marker.SetViewport(0.0, 0.0, 0.2, 0.2)  
        orientation_marker.SetEnabled(1)
        orientation_marker.InteractiveOff()
        orientation_marker.SetOutlineColor(0.5, 0.5, 0.5)  
        self.orientation_marker_widget = orientation_marker
    
    # Attributes
    def on_file_selected(self):
        item = self.file_list.currentItem()
        if not item:
            return

        file_name = item.text()
        if self.current_actor:
            self.current_actor.GetProperty().SetColor(1.0, 1.0, 1.0)

        self.current_actor = self.models[file_name]
        self.current_actor.GetProperty().SetColor(1.0, 1.0, 0.0)

        # Zoom to the selected actor
        bounds = self.current_actor.GetBounds()
        center = [
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0,
        ]
        self.renderer.GetActiveCamera().SetFocalPoint(center)

        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()
        self.set_table_value(file_name)

