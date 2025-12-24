import sys 
import os
import shutil

from PyQt5.QtWidgets import (
	QMainWindow, 
	QApplication, 
	QWidget, 
	QTabWidget, 
	QVBoxLayout, 
	QLabel, 
	QHBoxLayout,
	QGridLayout,
	QMessageBox
	)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt

from ui.sam_interactive_tab import SamInteractiveTabWidget
from ui.point_cloud_classification_tab import PointCloudClassificationTabWidget
from ui.roof_footprint_tab import RoofFootprintTabWidget
from ui.refine_rs_bo_tab import RefineRSBOTabWidget
from ui.lod1_tab import LOD1TabWidget
from ui.lod2_tab import LOD2TabWidget
from ui.cityjson_viewer_tab import CityjsonViewerTabWidget

from enums.layout_type import LayoutType

from utils.common import get_temp_dir


# Creating the main window 
class App(QMainWindow): 
	def __init__(self): 
		super().__init__() 
		self.title = "Cascade3D"
		self.left = 0
		self.top = 0
		self.width = 900
		self.height = 800
		self.setWindowTitle(self.title) 
		self.setWindowIcon(QIcon("public/icon/logo_title.png"))
		self.setGeometry(self.left, self.top, self.width, self.height) 

		self.tab_widget = MyTabWidget(self) 
		self.setCentralWidget(self.tab_widget) 

		self.show()
	
	def closeEvent(self, event):
        # Create a message box to ask for confirmation
		reply = QMessageBox.question(self, 'Confirmation', 
                                     "Are you sure you want to close the application?", 
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)
        
		if reply == QMessageBox.Yes:
			if os.path.exists(get_temp_dir()):
				shutil.rmtree(get_temp_dir())
            # If Yes is clicked, accept the close event
			event.accept()
		else:
            # If No is clicked, ignore the close event
			event.ignore()
		# return super().closeEvent(event)
	


# Creating tab widgets 
class MyTabWidget(QWidget): 
	def __init__(self, parent): 
		super(QWidget, self).__init__(parent)
		self.layout = QVBoxLayout(self)

		"""
			Header
		"""
		app_header = QGridLayout()
		# app_header = QHBoxLayout()
		
		# Add application image (replace with your image path)
		image_path = "public/icon/logo.png"  # Replace with your image path
		app_image = QLabel()
		app_image.setPixmap(QPixmap(image_path))
		app_image.setMaximumWidth(80)
		app_image.setContentsMargins(10, 10, 10, 10)
		# app_image.setFixedSize(60, 60)  # Adjust image size as needed
		app_header.addWidget(app_image, 0, 0)
		
		# Add application image (replace with your image path)
		image_path = "public/icon/logo_string.png"  # Replace with your image path
		app_image = QLabel()
		app_image.setPixmap(QPixmap(image_path))
		app_image.setMaximumWidth(220)
		app_image.setContentsMargins(10, 10, 10, 10)
		# app_image.setFixedSize(200, 60)  # Adjust image size as needed
		app_header.addWidget(app_image, 0, 1)

        # Add application title
		app_title = QLabel("Cadaster and Spatial Map Adjustment with Spatial Computation for Automatic Building Detection and 3D Generation")
		app_title.setFont(QFont("Arial", 10))  # Adjust font size and style as needed
		app_title.setWordWrap(True)
		app_title.setContentsMargins(10, 10, 10, 10)
		app_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		app_header.addWidget(app_title, 0, 2)

		# app_header.addLayout(left_header)
		# app_header.addLayout(right_header)
		self.layout.addLayout(app_header)

		"""
			Main app
		"""
		# Initialize tab screen 
		self.tabs = QTabWidget() 
		self.tabs.resize(300, 200) 

		# Add tabs 
		self.tabs.addTab(SamInteractiveTabWidget(LayoutType.vertical.value), "Interactive Digitization (BO)") 
		self.tabs.addTab(PointCloudClassificationTabWidget(LayoutType.vertical.value), "Point Clouds classification")
		self.tabs.addTab(RoofFootprintTabWidget(LayoutType.vertical.value), "Roof Structure (RS)")
		self.tabs.addTab(RefineRSBOTabWidget(LayoutType.vertical.value), "Refine RS/BO") 
		self.tabs.addTab(LOD1TabWidget(LayoutType.vertical.value), "LOD-1 Model Generation") 
		self.tabs.addTab(LOD2TabWidget(LayoutType.vertical.value), "LOD-2 Model Generation") 
		self.tabs.addTab(CityjsonViewerTabWidget(LayoutType.vertical.value), "3D Viewer") 

		self.tabs.setCurrentIndex(0)

		# Add tabs to widget 
		self.layout.addWidget(self.tabs) 
		# add tabs event handler
		self.tabs.tabBarClicked.connect(self.handle_clicked_tab)
		# Define stylesheets for individual tab buttons (adjust colors as needed)
		self.tabs.tabBar().setStyleSheet("""
            QTabBar::tab {
                background-color: #B6B6B6;
                color: white;
                padding: 5px 10px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #017FA7;
            }
        """)

		"""
			Footer
		"""
		app_footer = QHBoxLayout()
		app_footer.setAlignment(Qt.AlignCenter)

		footer_label = QLabel("This Application was developed by : ")
		app_footer.addWidget(footer_label)

		# Add application image (replace with your image path)
		engineering_faculty_logo = "public/icon/engineering_faculty_logo.png" 
		eng_fac_image = QLabel()
		eng_fac_image.setPixmap(QPixmap(engineering_faculty_logo))
		app_footer.addWidget(eng_fac_image)

		geodetic_department_logo = "public/icon/geodetic_department_logo.png"
		geo_dep_image = QLabel()
		geo_dep_image.setPixmap(QPixmap(geodetic_department_logo))
		app_footer.addWidget(geo_dep_image)

		self.layout.addLayout(app_footer)

		self.setLayout(self.layout) 

	def handle_clicked_tab(self, index):
        # Get the currently selected tab index
		selected_tab_index = self.tabs.currentIndex()

        # Define stylesheets for different tab states (adjust colors as needed)
		default_style = "background-color: white;"
		selected_style = "background-color: lightblue;"  # Color for selected tab

        # Set the stylesheet based on selected tab index
		if selected_tab_index == index:
			self.tabs.setStyleSheet(selected_style)
		else:
			self.tabs.setStyleSheet(default_style)

if __name__ == '__main__': 
	app = QApplication(sys.argv) 
	ex = App() 
	sys.exit(app.exec_()) 