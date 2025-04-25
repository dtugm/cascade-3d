from PyQt5 import QtWidgets, QtCore, QtGui
from enums.layout_type import LayoutType
from enums.file_extension import FileExtension

from ui.components.input_file import FileInputComponent

from pyqtspinner.spinner import WaitingSpinner

from ai.digitasi_interaktif.thread import MyThread
from ai.digitasi_interaktif.annotation_view import AnnotationView
from ai.digitasi_interaktif.annotation_scene import AnnotationScene
from ai.digitasi_interaktif.di_enum import Instructions

from ui.components.button import Button
from ui.components.checkbox import CheckBox
from ui.components.checkable_toolbutton import CheckableToolButton
from ui.components.text_area import TextArea
from ui.components.toolbutton_with_input_number import ToolbuttonWithInputNumberComponent

from utils.common import waiting_spinner_commands, get_current_time

import time

class SamInteractiveTabWidget(QtWidgets.QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent)

        self.set_current_action: CheckableToolButton | None = None
        self.set_layout(type)

        input_layer = FileInputComponent(
            "Load Layer (Raster)",
            ext=[FileExtension.Tif.value]
            )
        input_layer.file_selected.connect(self.handle_file_selected)
        self.layout.addWidget(input_layer)

        self.container = QtWidgets.QHBoxLayout()
        # self.image_container = QtWidgets.QWidget()
        
        self.set_canvas()
        self.set_toolbars()

        self.container.addWidget(self.toolbar_frame)
        self.container.addWidget(self.m_view)

        self.layout.addLayout(self.container)

        checkbox = CheckBox(label="Open the result directory")
        checkbox.clicked.connect(self.on_checkbox_clicked)
        self.layout.addWidget(checkbox)

        save_button = Button(name="Save Digitize Result")
        save_button.clicked.connect(self.on_save_button_clicked)
        self.layout.addWidget(save_button)

        self.log_text = TextArea()
        self.log_text.setFixedHeight(100)
        self.log_text.setMinimumWidth(120)
        self.layout.addWidget(self.log_text)

        self.set_spinner()

        # self.layout.addWidget(self.m_view)

    def on_save_button_clicked(self):
        # Open a file dialog for saving
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog  # Optional: Disable native dialog (optional)
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*.geojson)", options=options)

        if filename:
            self.m_scene.export(filename)

    def on_checkbox_clicked(self, state):
        self.m_scene.is_open_file = state

    def set_layout(self, type="horizontal"):
        if type == LayoutType.horizontal.value:
            self.layout = QtWidgets.QHBoxLayout(self)
        else:
            self.layout = QtWidgets.QVBoxLayout(self)

        self.setLayout(self.layout)

    def add_toolbars(self):
        # Create the widget
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        label = QtWidgets.QLabel("This is a label inside the widget")
        button = QtWidgets.QPushButton("Click Me")
        layout.addWidget(label)
        layout.addWidget(button)
        widget.setLayout(layout)
        widget.setStyleSheet("background-color: lightblue")  # Optional background color

        # # Create proxy widget and add it to the scene (with setItemIsTransformEnabled)
        self.proxy_widget = QtWidgets.QGraphicsProxyWidget()
        self.proxy_widget.setWidget(widget)
        # proxy_widget.setItemIsTransformEnabled(False)  # Keep widget at fixed position
        self.proxy_widget.setZValue(50)
        self.proxy_widget.setPos(QtCore.QPointF(10, 10))

    def set_toolbars(self):
        self.toolbar = QtWidgets.QVBoxLayout()
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setSpacing(0)

        self.toolbar_frame = QtWidgets.QFrame()
        self.toolbar_frame.setLayout(self.toolbar)
        stylesheet = "border: 1px solid gray; border-radius: 5px; padding: 0px 3px"
        self.toolbar_frame.setStyleSheet(stylesheet)
        self.toolbar_frame.setFixedWidth(80)

        point_icon = QtGui.QIcon("public/icon/Digitize Tool.svg")
        point_btn = CheckableToolButton(point_icon, "Add Building")
        point_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(point_btn, Instructions.Point))
        self.toolbar.addWidget(point_btn)

        red_points_icon = QtGui.QIcon("public/icon/Digitize Boundary Tool.svg")
        red_points_btn = CheckableToolButton(red_points_icon, "Red Points")
        red_points_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(red_points_btn, Instructions.Red_Point))
        self.toolbar.addWidget(red_points_btn)

        # tool button with number input 
        simplify_btn = ToolbuttonWithInputNumberComponent(
            defaultValue=1,
            tooltip="Simplify",
            icon="public/icon/Simplify Tool.svg",
        )
        simplify_btn.button.clicked.connect(lambda: self.on_toolbar_action_clicked(simplify_btn.button, Instructions.Simplify))
        simplify_btn.input.textChanged.connect(self.m_scene.set_simplify_tolerance)
        self.toolbar.addLayout(simplify_btn)

        self.simplify_all_btn = ToolbuttonWithInputNumberComponent(
            defaultValue=1,
            tooltip="Simplify All",
            icon="public/icon/Simplify All Tool.svg"
        )
        self.simplify_all_btn.button.clicked.connect(lambda: self.on_toolbar_action_clicked(self.simplify_all_btn.button, func=self.m_scene.simplify_all_polygons))
        self.simplify_all_btn.input.textChanged.connect(self.m_scene.set_simplify_all_tolerance)
        self.toolbar.addLayout(self.simplify_all_btn)

        merge_points_icon = QtGui.QIcon("public/icon/Merge Tool.svg")
        merge_points_btn = CheckableToolButton(merge_points_icon, "Merge Points")
        merge_points_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(merge_points_btn, Instructions.Merge_Point))
        self.toolbar.addWidget(merge_points_btn)

        regularisation_icon = QtGui.QIcon("public/icon/Regularize Tool.svg")
        regularisation_btn = CheckableToolButton(regularisation_icon, "Regularisation")
        regularisation_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(regularisation_btn, Instructions.Regularisation))
        self.toolbar.addWidget(regularisation_btn)

        remove_icon = QtGui.QIcon("public/icon/Delete Building.svg")
        remove_btn = CheckableToolButton(remove_icon, "Remove Building")
        remove_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(remove_btn, Instructions.Remove))
        self.toolbar.addWidget(remove_btn)

        remove_vertex_icon = QtGui.QIcon("public/icon/Delete Digitized Object.svg")
        remove_vertex_btn = CheckableToolButton(remove_vertex_icon, "Remove Vertex")
        remove_vertex_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(remove_vertex_btn, Instructions.Remove_Vertex))
        self.toolbar.addWidget(remove_vertex_btn)

        split_icon = QtGui.QIcon("public/icon/Splitter Tool.svg")
        split_btn = CheckableToolButton(split_icon, "Split Polygon")
        split_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(split_btn, Instructions.Split))
        self.toolbar.addWidget(split_btn)

    def on_toolbar_action_clicked(self, action: CheckableToolButton, intrusction_type=Instructions.No_Instruction, func = None):
        if self.set_current_action is not None:                                                         
            self.set_current_action.handle_click(is_checked=False)

        if intrusction_type == self.m_scene.current_instruction:
            self.m_scene.setCurrentInstruction(Instructions.No_Instruction)
        elif intrusction_type == Instructions.No_Instruction:
            action.handle_click(is_checked=True)
            self.m_scene.setCurrentInstruction(Instructions.No_Instruction)
            func()
            time.sleep(5)
            action.handle_click(is_checked=False)
        else:
            action.handle_click(is_checked=True)
            self.m_scene.setCurrentInstruction(intrusction_type)

        self.set_current_action = action
    
    def set_canvas(self):
        self.m_scene = AnnotationScene(self)
        self.m_view = AnnotationView(self.m_scene)
        self.m_view.setScene(self.m_scene)
        self.m_view.setMinimumHeight(500)

    def handle_process_start(self, msg):
        self.log_text.add_text(f"{get_current_time()}  {msg}")

        if msg in waiting_spinner_commands:
            self.spinner.start()

    def handle_process_running(self, msg):
        self.log_text.add_text(f"{get_current_time()}  {msg}")

    def handle_process_finished(self, msg):
        self.log_text.add_text(f"{get_current_time()}  {msg}")

        if msg in waiting_spinner_commands:
            self.spinner.stop()

    def set_spinner(self):
        self.spinner = WaitingSpinner(
            self,
            roundness=100.0,
            fade=70.0,
            radius=5.0,
            lines=7,
            line_length=20.0,
            line_width=5,
            speed=1.0,
            # color= QtGui.QColor("#E70448")
            color= QtGui.QColor("#017FA7")
        )
        
        self.m_scene.started.connect(self.handle_process_start)
        self.m_scene.finished.connect(self.handle_process_finished)

        self.layout.addWidget(self.spinner)

        
    @QtCore.pyqtSlot()
    def spinner_start(self):
        self.spinner.start()
        self.setEnabled(False)
    
    @QtCore.pyqtSlot()
    def spinner_stop(self):
        self.spinner.stop()
        self.setEnabled(True)

    def handle_file_selected(self, filename):
        def set_loaded_image():
            self.m_scene.remove_all_polygons()

        self.m_scene.initiate_scene_variables()

        thread = MyThread(target=self.m_scene.load_image, args=(filename,))
        thread.finished_signal.connect(set_loaded_image)
        thread.start()
        print(filename)