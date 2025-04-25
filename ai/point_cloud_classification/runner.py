from PyQt5.QtCore import QObject, pyqtSignal
from .interface import PointCloudClassificationParams
from enums.point_cloud_classification import AlgorithmOptions, FeatureOptions

import time
import pickle
import numpy as np
import laspy
import xgboost as xgb

class PointCloudClassification(QObject):
  progress = pyqtSignal(str, int)
  finished = pyqtSignal(str)
  error = pyqtSignal(str)

  def __init__(self, params: PointCloudClassificationParams, parent = None):
    super().__init__(parent)
    self.args: PointCloudClassificationParams = params

    self.x_column_averages = [0.0, 0.0]  # Initialize averages for X columns
    if params.features == FeatureOptions.INTENSITY.value:
      self.feat_to_use = [0, 1, 2, 3]   
    elif params.features == FeatureOptions.RGB.value:
      self.feat_to_use = [0, 1, 2, 3, 4, 5]

  def read_data(self):
    lasfile = laspy.read(self.args.point_cloud_path)
    x = lasfile.x
    y = lasfile.y
    z = lasfile.z

    if self.args.features == FeatureOptions.INTENSITY.value:
      I = lasfile.intensity
      X_train = np.column_stack((x, y, z, I))
    elif self.args.features == FeatureOptions.RGB.value:
      r = lasfile.red
      g = lasfile.green
      b = lasfile.blue
      X_train = np.column_stack((x, y, z, r, g, b))
    
    return X_train

  def write_classification(self, X, Y):
    header = laspy.LasHeader(point_format=2, version="1.2")
    las = laspy.LasData(header)
    las.x = X[:, 0]
    las.y = X[:, 1]
    las.z = X[:, 2]

    if self.args.features == FeatureOptions.INTENSITY.value:
      las.intensity = X[:, 3]
    elif self.args.features == FeatureOptions.RGB.value:
      las.red = X[:, 3]
      las.green = X[:, 4]
      las.blue = X[:, 5]

    reverse_mapping = {0: 2, 1: 5, 2: 6}
    # Class: 2 = ground, 5 = vegetation, 6 = building
    Y = np.array([reverse_mapping[label] for label in Y])
    Y = np.rint(Y).astype(np.uint8)
    las.classification = Y[:]

    ext = 'laz' if self.args.features == FeatureOptions.INTENSITY.value else 'las'
    las.write(f"{self.args.output_path}.{ext}")

  # xg boost
  def predict_model(self, model, X_test):
    dtest = xgb.DMatrix(data=X_test[:, self.feat_to_use])
    return model.predict(dtest)
  
  def run(self):
    try:
      start = time.time() 
      
      self.progress.emit('Memuat Model ...', 0)
      model = pickle.load(open(self.args.model, 'rb'))

      self.progress.emit('Loading data ...', 10)
      X = self.read_data()
      
      self.progress.emit('Classifying the dataset ...', 20)
      if self.args.algorithm == AlgorithmOptions.RF.value:
        Y_pred = model.predict(X[:, self.feat_to_use])
      elif self.args.algorithm == AlgorithmOptions.XG_BOOST.value:
        Y_pred = self.predict_model(model, X)

      self.progress.emit('Saving ...', 90)
      self.write_classification(X, Y_pred)

      end = time.time()
      self.finished.emit('Data classified in: {}'.format(end - start))
    except Exception as e:
      print(str(e))
      self.error.emit(str(e))
  