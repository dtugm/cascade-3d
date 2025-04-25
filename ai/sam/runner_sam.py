import numpy as np
import pandas as pd
import os
from matplotlib import pyplot as plt
import torch
import cv2
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor
import os
from utils.common import get_root_dir

class SAM:
  def __init__(self) -> None:
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
    self.model_checkpoint = os.path.join(get_root_dir(), "ai", "sam", "model", "sam_vit_h_4b8939.pth")

    # SAM
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model_type = "vit_h"

    sam = sam_model_registry[model_type](checkpoint=self.model_checkpoint)
    sam.to(device=device)

    self.predictor = SamPredictor(sam)

  def load_image(self, image):
    # self.file_path = 'files/image.jpg'
    # self.image = cv2.cvtColor(cv2.imread(self.file_path), cv2.COLOR_BGR2RGB)
    image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)

    # set image to the sam predictor
    self.predictor.set_image(image)

    # height, width, _ = self.image.shape
    # self.image_res = np.zeros((height, width), np.uint8)


  def predict(self, points, red_points):
    points_array = []
    points_label = []
    for point in points:
      # points_array.append([point[0], point[1]])
      points_array.append([point.x(), point.y()]) # temp
      points_label.append(1)

    for point in red_points:
      # points_array.append([point[0], point[1]])
      points_array.append([point.x(), point.y()])
      points_label.append(0)
      
    # input_point = np.array([[500, 500], [500, 510], [500, 520], [500, 530], [500, 540], [500, 560], [500, 570]])
    # input_label = np.array([1, 1, 1, 1, 1, 1, 1])
    input_points = np.array(points_array)
    input_labels = np.array(points_label)

    masks, scores, logits = self.predictor.predict(
        point_coords=input_points,
        point_labels=input_labels,
        multimask_output=True,
    )

    # Apply some noise reduction (optional)
    max_score_idx = np.argmax(scores)
    min_score_idx = np.argmin(scores)
    avg_score_idx = max_score_idx
    for idx, score in enumerate(scores):
      if idx not in [min_score_idx, max_score_idx]:
        avg_score_idx = idx
    mask = np.array(masks[max_score_idx], dtype=np.uint8)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Iterate over contours and draw outlines
    # for cnt in contours:
    #   cv2.drawContours(self.image_res, [cnt], 0, (255, 255, 255), 2)  # Change (255, 0, 0) for desired outline color

    if len(contours) != 0:
      contour = max(contours, key=cv2.contourArea)
      return contour
    
      # eps = 0.01
      # peri = cv2.arcLength(contour, True)
      # approx = cv2.approxPolyDP(contour, eps*peri, True)

      # return approx
    else:
      return contours
