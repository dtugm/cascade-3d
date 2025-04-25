from PyQt5 import QtWidgets, QtCore
from enums.layout_type import LayoutType
from enums.message_box_type import MessageBoxTypeEnum
from enums.file_extension import FileExtension

from ui.components.input_file import FileInputComponent
from ui.components.input_directory import DirectoryInputComponent
from ui.components.checkbox import CheckBox
from ui.components.button import Button
from ui.components.text_area import TextArea
from ui.components.button_collapse import CollapseButton

from ai.lod_generation.interface import Py3dModelConfig
from ai.lod_generation.runner_lod2 import GenerateLOD2

from utils.common import get_current_time, get_base_dir, set_output_path, set_text_with_color

import subprocess
import os

from ui.components.message_box import CustomMessageBox

class LOD2TabWidget(QtWidgets.QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent)

        self.set_layout(type)

        # input
        self.dtm = FileInputComponent(
            "Load DTM",
            button_font_color="white",
            ext=[FileExtension.Tif.value]
        )
        self.layout.addWidget(self.dtm)

        self.dsm = FileInputComponent(
            "Load DSM",
            button_font_color="white",
            ext=[FileExtension.Tif.value]
        )
        self.layout.addWidget(self.dsm)

        self.rs = FileInputComponent(
            "Load Roof Structure (RS)",
            button_font_color="white",
            ext=[FileExtension.Shp.value, FileExtension.Geojson.value]
        )
        self.layout.addWidget(self.rs)

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
            defaultValue=os.path.join(get_base_dir(), "Cascade 3D", "output", "lod2")
        )
        self.layout.addWidget(self.result)

        on_finished = CheckBox("Notify me once the process is finished")
        on_finished.clicked.connect(self.on_finished_checkbox_clicked)
        self.layout.addWidget(on_finished)
        open_file = CheckBox("Open the result directory")
        open_file.clicked.connect(self.on_open_file_checkbox_clicked)
        self.layout.addWidget(open_file)

        self.button = Button("Generate LOD 2")
        self.button.clicked.connect(self.on_button_clicked)
        self.layout.addWidget(self.button)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.log_text = TextArea()
        # self.log_text.setFixedHeight(100)
        # self.log_text.setMinimumWidth(120)
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
                "Generating LOD2 Successful",
                parent=self,
                icon=MessageBoxTypeEnum.Information.value
            )
            message_box.show()

        if self.is_open_file:
            subprocess.Popen(f"explorer {self.result.dir_name}")
    
    def set_layout(self, type=LayoutType.horizontal.value):
        if type == LayoutType.horizontal.value:
            self.layout = QtWidgets.QHBoxLayout(self)
        else:
            self.layout = QtWidgets.QVBoxLayout(self)

        self.setLayout(self.layout)

    def on_button_clicked(self):
        output_path = set_output_path(self.bo.filename, self.result.dir_name, "json", is_include_timestamp=True)
        print(f"output path {output_path}")
        config = Py3dModelConfig(
            input_dem=self.dtm.filename,
            input_surface=self.dsm.filename,
            input_building=self.bo.filename,
            input_roof=self.rs.filename,
            building_type="Solid",
            output_file=output_path
        )
        
        # thread objec
        self.qthread = QtCore.QThread()
        # worker object
        self.worker = GenerateLOD2(config)
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
