from PyQt5 import QtWidgets, QtCore
from enums.layout_type import LayoutType
from enums.message_box_type import MessageBoxTypeEnum
from enums.file_extension import FileExtension

from ui.components.input_file import FileInputComponent
from ui.components.input_directory import DirectoryInputComponent
from ui.components.checkbox import CheckBox
from ui.components.button import Button
from ui.components.text_area import TextArea
from ui.components.message_box import CustomMessageBox
from ui.components.button_collapse import CollapseButton

from ai.roof_footprint.interface import RoofFootprintParams
from ai.roof_footprint.runner_roof_footprint import GenerateRoofFootprint

from utils.common import get_current_time, get_base_dir, set_output_path, set_text_with_color

import subprocess
import os

class RoofFootprintTabWidget(QtWidgets.QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent)

        self.set_layout(type)

        # input
        self.ohm = FileInputComponent(
            "Load BHM",
            button_font_color="white",
            ext=[FileExtension.Tif.value]
        )
        self.layout.addWidget(self.ohm)

        self.bo = FileInputComponent(
            "Load Building Outline (BO)",
            button_font_color="white",
            ext=[FileExtension.Shp.value, FileExtension.Geojson.value]
        )
        self.layout.addWidget(self.bo)

        # additional parameter
        self.additional_params = CollapseButton("Additional Parameters")
        self.layout.addWidget(self.additional_params)
        self.additional_params.btn_state_signal.connect(self.on_additional_params_btn_clicked)

        self.result = DirectoryInputComponent(
            "Output Directory",
            button_font_color="white",
            defaultValue=os.path.join(get_base_dir(), "Cascade 3D", "output", "roof footprint")
        )
        self.layout.addWidget(self.result)

        on_finished = CheckBox("Notify me once the process is finished")
        on_finished.clicked.connect(self.on_finished_checkbox_clicked)
        self.layout.addWidget(on_finished)
        open_file = CheckBox("Open the result directory")
        open_file.clicked.connect(self.on_open_file_checkbox_clicked)
        self.layout.addWidget(open_file)

        # runner button
        self.button = Button("Generate Roof Structure")
        self.button.clicked.connect(self.on_button_clicked)
        self.layout.addWidget(self.button)

        # progres bar
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.log_text = TextArea()
        self.layout.addWidget(self.log_text)

        # Variables
        self.is_open_file = False
        self.is_finished_pop_up = False
        # initiate additional params as invisible
        self.on_additional_params_btn_clicked(False)

    def on_additional_params_btn_clicked(self, visibility: bool):
        self.result.setVisible(visibility)

    def on_open_file_checkbox_clicked(self, state):
        self.is_open_file = state
    
    def on_finished_checkbox_clicked(self, state):
        self.is_finished_pop_up = state

    def handle_process_error(self, msg):
        message = set_text_with_color(f"{get_current_time()}  Error : {msg}", "red")
        self.log_text.add_text(message)
        self.progress_bar.setValue(100)

    def handle_process_running(self, msg, number):
        self.log_text.add_text(f"{get_current_time()}  {msg}")
        self.progress_bar.setValue(int(number))

    def handle_process_finished(self, msg, number):
        message = set_text_with_color(f"{get_current_time()}  {msg}", "blue")
        self.log_text.add_text(message)
        self.progress_bar.setValue(int(number))
        
        if self.is_finished_pop_up:
            message_box = CustomMessageBox(
                "Info",
                "Generating Roof Footprint Successful",
                parent=self,
                icon=MessageBoxTypeEnum.Information.value
            )
            message_box.show()

        if self.is_open_file:
            folderpath = os.path.dirname(self.result.dir_name)
            path = os.path.realpath(folderpath)
            subprocess.Popen(f"explorer {self.result.dir_name}")
    
    def set_layout(self, type=LayoutType.horizontal.value):
        if type == LayoutType.horizontal.value:
            self.layout = QtWidgets.QHBoxLayout(self)
        else:
            self.layout = QtWidgets.QVBoxLayout(self)

        self.setLayout(self.layout)

    def on_button_clicked(self):   
        output_path = set_output_path(self.bo.filename, self.result.dir_name, "shp", is_include_timestamp=True)
        params = RoofFootprintParams(
            ohm_path=self.ohm.filename,
            bo_path=self.bo.filename,
            output_file=output_path
        )
        # thread objec
        self.qthread = QtCore.QThread()
        # worker object
        self.worker = GenerateRoofFootprint(params)
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