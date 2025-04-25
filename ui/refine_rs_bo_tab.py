from PyQt5 import QtWidgets, QtCore, QtGui
from enums.layout_type import LayoutType
from enums.file_extension import FileExtension
from enums.refine_rs_bo.instruction_type import Instructions
from enums.message_box_type import MessageBoxTypeEnum

from ai.refine_rs_bo.view_annotation import AnnotationView
from ai.refine_rs_bo.scene_annotation import AnnotationScene
from ui.components.message_box import CustomMessageBox

from ui.components.input_file import FileInputComponent
from ui.components.button import Button
from ui.components.checkbox import CheckBox
from ui.components.checkable_toolbutton import CheckableToolButton
from ui.components.toolbutton_with_input_number import ToolbuttonWithInputNumberComponent

import time

class RefineRSBOTabWidget(QtWidgets.QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent)

        self.set_current_action: CheckableToolButton | None = None
        self.set_layout(type)

        input_layer = FileInputComponent(
            "Load Layer (Raster)",
            ext=[FileExtension.Tif.value]
            )
        input_layer.file_selected.connect(self.handle_input_layer)
        self.layout.addWidget(input_layer)

        input_rs = FileInputComponent(
            "Load Roof Structure",
            ext=[FileExtension.Geojson.value, FileExtension.Shp.value]
            )
        input_rs.file_selected.connect(self.handle_input_rs)
        self.layout.addWidget(input_rs)

        input_bo = FileInputComponent(
            "Load Building Outline",
            ext=[FileExtension.Geojson.value, FileExtension.Shp.value]
            )
        input_bo.file_selected.connect(self.handle_input_bo)
        self.layout.addWidget(input_bo)

        self.container = QtWidgets.QHBoxLayout()
        
        self.set_canvas()
        self.set_toolbars()

        self.container.addWidget(self.toolbar_frame)
        self.container.addWidget(self.m_view)

        self.layout.addLayout(self.container)

        checkbox = CheckBox(label="Open the result directory")
        checkbox.clicked.connect(self.on_checkbox_clicked)
        self.layout.addWidget(checkbox)

        save_button = Button(name="Save Digitze Result")
        save_button.clicked.connect(self.on_save_button_clicked)
        self.layout.addWidget(save_button)

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


    def set_toolbars(self):
        self.toolbar = QtWidgets.QVBoxLayout()
        self.toolbar.setAlignment(QtCore.Qt.AlignTop)
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setSpacing(0)

        self.toolbar_frame = QtWidgets.QFrame()
        self.toolbar_frame.setLayout(self.toolbar)
        stylesheet = "border: 1px solid gray; border-radius: 5px; padding: 0px 3px"
        self.toolbar_frame.setStyleSheet(stylesheet)
        self.toolbar_frame.setFixedWidth(80)

        point_icon = QtGui.QIcon("public/icon/Digitize Tool.svg")
        point_btn = CheckableToolButton(point_icon, "Move Building Vertex Coordinates")
        point_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(point_btn, Instructions.Point))
        self.toolbar.addWidget(point_btn)

        remove_vertex_icon = QtGui.QIcon("public/icon/Delete Digitized Object.svg")
        remove_vertex_btn = CheckableToolButton(remove_vertex_icon, "Remove vertex")
        remove_vertex_btn.clicked.connect(lambda: self.on_toolbar_action_clicked(remove_vertex_btn, Instructions.Remove_Vertex))
        self.toolbar.addWidget(remove_vertex_btn)

        # tool button with number input 
        simplify_btn = ToolbuttonWithInputNumberComponent(
            defaultValue=1,
            tooltip="Simplify",
            icon="public/icon/Simplify Tool.svg",
        )
        simplify_btn.button.clicked.connect(lambda: self.on_toolbar_action_clicked(simplify_btn.button, Instructions.Simplify))
        simplify_btn.input.textChanged.connect(self.m_scene.set_simplify_tolerance)
        self.toolbar.addLayout(simplify_btn)


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

    def handle_input_layer(self, filename):
        self.m_scene.initiate_scene_variables()

        self.m_scene.load_image(filename)

        self.m_scene.remove_all_polygons()

    def handle_input_rs(self, filename):
        if self.m_scene.image is not None:
            self.m_scene.load_rs(filename)
        else:
            message_box = CustomMessageBox(
                "Warning",
                "You have to choose the raster file first",
                parent=self,
                icon=MessageBoxTypeEnum.Warning.value
            )
            message_box.show()

    def handle_input_bo(self, filename):
        if self.m_scene.image is not None:
            self.m_scene.load_bo(filename)
        else:
            message_box = CustomMessageBox(
                "Warning",
                "You have to choose the tif file first",
                parent=self,
                icon=MessageBoxTypeEnum.Warning.value
            )
            message_box.show()