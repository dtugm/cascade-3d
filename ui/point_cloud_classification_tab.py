from PyQt5 import QtWidgets, QtCore
from enums.layout_type import LayoutType
from enums.message_box_type import MessageBoxTypeEnum
from enums.file_extension import FileExtension

from ui.components.input_file import FileInputComponent
from ui.components.checkbox import CheckBox
from ui.components.button import Button
from ui.components.text_area import TextArea
from ui.components.message_box import CustomMessageBox
from ui.components.button_collapse import CollapseButton
from ui.components.dropdown import DropdownComponent
from ui.components.input_number import NumberInputComponent
from ui.components.input_directory import DirectoryInputComponent
from ui.components.input_filename import FilenameInputComponent

from ai.dgcnn_rgb_intensity.interface import DGCNNParams
from ai.dgcnn_rgb_intensity.runner_dgcnn_rgb_intensity import DGCNNIntensity
from ai.dgcnn_rgb.runner_dgcnn_rgb import DGCNN

from utils.common import get_current_time, set_text_with_color, get_base_dir
from enums.point_cloud_classification import AlgorithmOptions, FeatureOptions

import subprocess
import os

class PointCloudClassificationTabWidget(QtWidgets.QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent)

        self.set_layout(type)

        self.algorithm = DropdownComponent(
            label="Select Algorithm",
            options=["Deep Learning", "Machine Learning - Random Forest (CPU Only)", "Machine Learning - XGBoost"],
            dropdown_name="algorithm"
            )
        self.algorithm.setVisible(False)
        self.algorithm.on_changed.connect(self.on_algorithm_or_features_changed)    
        self.layout.addWidget(self.algorithm)

        self.features = DropdownComponent(
            label="Select Features",
            options=["XYZ RGB", "XYZ Intensity"],
            dropdown_name="features",
            )
        self.features.on_changed.connect(self.on_algorithm_or_features_changed)
        self.layout.addWidget(self.features)

        # input
        self.point_cloud = FileInputComponent(
            "Load Point Cloud",
            button_font_color="white",
            ext=[FileExtension.Las.value]
        )
        self.layout.addWidget(self.point_cloud)

        # additional parameter``
        self.additional_params = CollapseButton("Additional Parameters")
        self.layout.addWidget(self.additional_params)
        self.additional_params.btn_state_signal.connect(self.on_additional_params_btn_clicked)

        self.result_file = FilenameInputComponent(
            "Select Output File",
            button_font_color="white",
            filetype="",
            defaultValue=os.path.join(get_base_dir(), "Cascade 3D", "output", "point_cloud_classification", "result")
        )
        self.result_file.setVisible(False)  # Initially visible
        self.layout.addWidget(self.result_file)
        
        self.result_dir = DirectoryInputComponent(
            "Select Output Directory",
            button_font_color="white",
            defaultValue=os.path.join(get_base_dir(), "Cascade 3D", "output", "point_cloud_classification")
        )
        self.result_dir.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.result_dir)

        self.model = FileInputComponent(
            "Model",
            button_font_color="white",
            defaultValue=os.path.join(get_base_dir(), "cascade-3d", "ai", "point_cloud_classification", "model", "DGCNN_RGB.t7")
        )
        self.layout.addWidget(self.model)
        
        self.batch_size = NumberInputComponent(
            label="Input Batch Size",
            defaultValue=16,
            type="int"
            )
        self.batch_size.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.batch_size)

        on_finished = CheckBox("Notify me once the process is finished")
        on_finished.clicked.connect(self.on_finished_checkbox_clicked)
        self.layout.addWidget(on_finished)
        open_file = CheckBox("Open the result directory")
        open_file.clicked.connect(self.on_open_file_checkbox_clicked)
        self.layout.addWidget(open_file)

        # runner button
        self.button = Button("Run")
        self.button.clicked.connect(self.on_button_clicked)
        self.layout.addWidget(self.button)

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
        self.additional_params_visibility: bool = False
        self.on_additional_params_btn_clicked(False)

    def on_algorithm_or_features_changed(self):
        algo = self.algorithm.get_selected_item
        feat = self.features.get_selected_item

        dir = os.path.join(get_base_dir(), "cascade-3d", "ai", "point_cloud_classification", "model")
        modelpath = None
        model_files = {
            (AlgorithmOptions.RF.value, FeatureOptions.RGB.value): "RF_RGB.pkl",
            (AlgorithmOptions.RF.value, FeatureOptions.INTENSITY.value): "RF_I.pkl",
            (AlgorithmOptions.DGCNN.value, FeatureOptions.RGB.value): "DGCNN_RGB.t7",
            (AlgorithmOptions.DGCNN.value, FeatureOptions.INTENSITY.value): "DGCNN_I.t7",
            (AlgorithmOptions.XG_BOOST.value, FeatureOptions.RGB.value): "XGBoost_RGB.pkl",
            (AlgorithmOptions.XG_BOOST.value, FeatureOptions.INTENSITY.value): "XGBoost_I.pkl",
        }
        modelpath = os.path.join(dir, model_files.get((algo, feat)))
        self.model.set_value(modelpath)

        if algo == AlgorithmOptions.DGCNN.value and self.additional_params_visibility:
            self.batch_size.setVisible(True)
            self.result_dir.setVisible(True)
            self.result_file.setVisible(False)
        elif self.additional_params_visibility:
            self.batch_size.setVisible(False)
            self.result_dir.setVisible(False)
            self.result_file.setVisible(True)
    
    def set_layout(self, type=LayoutType.horizontal.value):
        if type == LayoutType.horizontal.value:
            self.layout = QtWidgets.QHBoxLayout(self)
        else:
            self.layout = QtWidgets.QVBoxLayout(self)

        self.setLayout(self.layout)

    def on_additional_params_btn_clicked(self, visibility: bool):
        self.additional_params_visibility = visibility
        self.model.setVisible(visibility)

        if self.algorithm.get_selected_item == AlgorithmOptions.DGCNN.value:
            self.batch_size.setVisible(visibility)
            self.result_dir.setVisible(visibility)
            self.result_file.setVisible(False)
        else:
            self.result_dir.setVisible(False)
            self.result_file.setVisible(visibility)

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

    def handle_process_finished(self, msg):
        message = set_text_with_color(f"{get_current_time()}  {msg}", "blue")
        self.log_text.add_text(message)
        self.progress_bar.setValue(100)

        if self.is_finished_pop_up:
            message_box = CustomMessageBox(
                "Info",
                "Processing Completed Successfully",
                parent=self,
                icon=MessageBoxTypeEnum.Information.value
            )
            message_box.show()

        if self.is_open_file:
            result = self.result_dir.dir_name if self.algorithm.get_selected_item == AlgorithmOptions.DGCNN.value else self.result_file.filename
            folderpath = os.path.dirname(result)
            path = os.path.realpath(folderpath)
            subprocess.Popen(f"explorer {path}")

    def on_button_clicked(self):   
        if self.algorithm.get_selected_item == AlgorithmOptions.DGCNN.value and self.features.get_selected_item == FeatureOptions.RGB.value:
            params = DGCNNParams(
                point_cloud=self.point_cloud.filename,
                batch_size=self.batch_size.input_value,
                output_path=self.result_dir.dir_name,
                model=self.model.filename
            )
            # worker object
            self.worker = DGCNN(params)
        elif self.algorithm.get_selected_item == AlgorithmOptions.DGCNN.value and self.features.get_selected_item == FeatureOptions.INTENSITY.value:
            params = DGCNNParams(
                point_cloud=self.point_cloud.filename,
                batch_size=self.batch_size.input_value,
                output_path=self.result_dir.dir_name,
                model=self.model.filename
            )
            # worker object
            self.worker = DGCNNIntensity(params)

        # thread object
        self.qthread = QtCore.QThread()
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