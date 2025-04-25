from PyQt5 import QtWidgets, QtGui, QtCore
from .annotation_scene import AnnotationScene
from .annotation_view import AnnotationView
from .toggle_action import ToggleAction
from .thread import MyThread
from .di_enum import Instructions
from functools import partial
from pyqtspinner.spinner import WaitingSpinner

class AnnotationWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(AnnotationWindow, self).__init__(parent)
        self.m_scene = AnnotationScene(self)
        self.m_view = AnnotationView(self.m_scene)
        self.m_view.setScene(self.m_scene)

        self.setCentralWidget(self.m_view)
        self.create_menus()
        self.create_toolbars()

        self.spinner = WaitingSpinner(
            self,
            roundness=100.0,
            fade=70.0,
            radius=40.0,
            lines=10,
            line_length=50.0,
            line_width=10,
            speed=1.0,
            color= QtGui.QColor("black")
        )
        self.m_scene.started.connect(self.spinner_start)
        self.m_scene.finished.connect(self.spinner_stop)

        self.set_current_action: ToggleAction | None = None

        QtWidgets.QShortcut(QtCore.Qt.Key_Escape, self, activated=partial(self.m_scene.setCurrentInstruction, Instructions.No_Instruction))

    @QtCore.pyqtSlot()
    def spinner_start(self):
        self.spinner.start()
        self.setEnabled(False)
    
    @QtCore.pyqtSlot()
    def spinner_stop(self):
        self.spinner.stop()
        self.setEnabled(True)

    def create_toolbars(self):
        self.toolbar = QtWidgets.QToolBar("Main Toolbar")

        simplify_icon = QtGui.QIcon("public/icon/simplify.png")
        self.simplify_action = ToggleAction("Simplify", simplify_icon)

        simplify_all_icon = QtGui.QIcon("public/icon/simplify.png")
        self.simplify_all_action = ToggleAction("Simplify All", simplify_all_icon)

        merge_points_icon = QtGui.QIcon("public/icon/merge.png")
        self.merge_points_action = ToggleAction("Merge Points", merge_points_icon)
        
        merge_icon = QtGui.QIcon("public/icon/checklist.png")
        self.merge_action = ToggleAction("Merged", merge_icon)

        red_point_icon = QtGui.QIcon("public/icon/red flag.png")
        self.red_point_action = ToggleAction("Red Flag", red_point_icon)

        regularisation_icon = QtGui.QIcon("public/icon/regularisation.png")
        self.regularisation_action = ToggleAction("Regularisation", regularisation_icon)

        point_icon = QtGui.QIcon("public/icon/point.png")
        self.point_action = ToggleAction("Add Building", point_icon)

        remove_icon = QtGui.QIcon("public/icon/remove.png")
        self.remove_action = ToggleAction("Remove Building", remove_icon)

        self.toolbar.addAction(self.simplify_action)
        self.toolbar.addAction(self.simplify_all_action)
        self.toolbar.addAction(self.remove_action)
        self.toolbar.addAction(self.point_action)
        self.toolbar.addAction(self.red_point_action)
        self.toolbar.addAction(self.regularisation_action)
        self.toolbar.addAction(self.merge_points_action)
        self.toolbar.addAction(self.merge_action)
        self.addToolBar(self.toolbar)

        self.simplify_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.simplify_action, Instructions.Simplify))
        self.simplify_all_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.simplify_all_action, func=self.m_scene.simplify_all_polygons))
        self.merge_points_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.merge_points_action, Instructions.Merge_Point))
        self.merge_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.merge_action, func=self.m_scene.merge_polygons))
        self.remove_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.remove_action, Instructions.Remove))
        self.point_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.point_action,  Instructions.Point))
        self.red_point_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.red_point_action,  Instructions.Red_Point))
        self.regularisation_action.triggered.connect(lambda: self.on_toolbar_action_clicked(self.regularisation_action,  Instructions.Regularisation))
    
    def on_toolbar_action_clicked(self, action: ToggleAction, intrusction_type=Instructions.No_Instruction, func = None):
        if self.set_current_action is not None:                                                         
            self.set_current_action.handle_click(is_cheked=False)

        if intrusction_type == Instructions.No_Instruction:
            action.handle_click(not action.isChecked())
            self.m_scene.setCurrentInstruction(Instructions.No_Instruction)
            func()
        elif intrusction_type == self.m_scene.current_instruction:
            self.m_scene.setCurrentInstruction(Instructions.No_Instruction)
        else:
            action.handle_click(is_cheked=True)
            self.m_scene.setCurrentInstruction(intrusction_type)

        self.set_current_action = action

    def create_menus(self):
        # File
        menu_file = self.menuBar().addMenu("File")
        load_image_action = menu_file.addAction("&Load Image")
        load_image_action.triggered.connect(self.load_image)

        export_action = menu_file.addAction("Export as Geojson")
        export_action.triggered.connect(self.m_scene.export)

    @QtCore.pyqtSlot()
    def load_image(self):
        def set_loaded_image():
            self.m_view.fitInView(self.m_scene.image_item, QtCore.Qt.KeepAspectRatio)
            self.m_view.centerOn(self.m_scene.image_item)

            # remove all polygons before loading an image
            self.m_scene.remove_all_polygons()

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 
            "Open Image",
            QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.PicturesLocation), #QtCore.QDir.currentPath(), 
            "All Files (*.tif)")
            # "Image Files (*.png *.jpg *.bmp)")
        if filename:
            self.m_scene.initiate_scene_variables()

            thread = MyThread(target=self.m_scene.load_image, args=(filename,))
            thread.finished_signal.connect(set_loaded_image)
            thread.start()