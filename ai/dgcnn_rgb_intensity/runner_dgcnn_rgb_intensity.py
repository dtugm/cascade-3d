# 6. Define testing function
from PyQt5 import QtCore

CUDA_LAUNCH_BLOCKING="1"

"""
Author: Benny
Date: Nov 2019
"""
import os
import shutil
from .data_utils.dataLoader import ScannetDatasetWholeScene
from .models.dgcnn_sem_seg import dgcnn_sem_seg
import torch
import torch.nn as nn
from pathlib import Path
import sys
import numpy as np
import time
import re

from .data_utils.split_merge_las import *
from .data_utils.merge_las import append_to_las

from utils.io_las import save_las
from utils.dgcnn import add_vote
from utils.common import get_filename_from_filepath, get_current_time_for_filename

from .interface import DGCNNParams

BASE_DIR = os.path.dirname(os.path.abspath(os.getcwd()))
ROOT_DIR = BASE_DIR
CUR_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(ROOT_DIR, 'models'))

classes = ['0', '1', '2']
classes = ['0', '1', '2']
class2label = {cls: i for i, cls in enumerate(classes)}
seg_classes = class2label
seg_label_to_cat = {}
for i, cat in enumerate(seg_classes.keys()):
    seg_label_to_cat[i] = cat

class DGCNNIntensity(QtCore.QObject):
    progress = QtCore.pyqtSignal(str, int)
    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, params: DGCNNParams, parent=None):
        super().__init__(parent)

        self.args: DGCNNParams = params

    def run(self):
        try:
            self.progress.emit("Start", 0)
            
            # Record the start time
            start_time = time.time()
                
            self.progress.emit("Read data", 5)
            data = read_las(self.args.point_cloud)
            
            self.xy_min = np.amin(data, axis=0)[0:2]
            data[:, 0:2] -= self.xy_min
            zeros_column = np.ones((data.shape[0], 1))
            data = np.hstack((data, zeros_column))
            
            data_dir = os.path.join(CUR_DIR, 'data', 'sem_seg_data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            num_blocks_x, num_blocks_y = calculate_block_size(data, self.args.block_size)
            print("Number of blocks in x direction:", num_blocks_x)
            print("Number of blocks in y direction:", num_blocks_y)
            blocks = split_array(data, num_blocks_x, num_blocks_y, self.args.block_size)
            print("Total number of blocks generated:", len(blocks))   
            print("Split data into blocks")
            
            self.progress.emit("Split data into blocks", 10)
            for i, block in enumerate(blocks):
                print("Block", i, "contains", len(block), "points")     
                block_data_bytes = block.tobytes()
                
                # Calculate the size of block_data in bytes
                block_data_size = len(block_data_bytes)
                
                # Check if the size is below 1 MB (1,048,576 bytes)
                if block_data_size > 1_048_576:
                    filename_offground_npy = os.path.join(data_dir, f'Area_{i}.npy')
                    # Save the block_data if it meets the size criteria
                    np.save(filename_offground_npy, block)
                    print(f'Saved: {filename_offground_npy} (size: {block_data_size} bytes)')
                else:
                    print(f'Skipped: Block data size {block_data_size} bytes < 1 MB')
                
            
            areas = []
            # Iterate over all files in the folder
            for filename in os.listdir(data_dir):
                # Check if the filename matches the pattern "Area_<number>.npy"
                match = re.match(r'Area_(\d+)\.npy', filename)
                if match:
                    # Extract the number and convert it to an integer
                    number = int(match.group(1))
                    # Add the number to the list
                    areas.append(number)

            # Sort the list of numbers
            areas.sort()
            
            # Buat folder untuk per block
            filename = f"{get_filename_from_filepath(self.args.point_cloud)}_{get_current_time_for_filename()}"
            self.visual_dir = os.path.join(self.args.output_path, "visual", filename) 
            self.visual_dir = Path(self.visual_dir)
            self.visual_dir.mkdir(parents=True, exist_ok=True)
            
            self.progress.emit("Start Classification", 20)
            print("Start classification")
            for index, test_area in enumerate(areas):
                print("Classify Block ", test_area)
                self.classification(filename, test_area)

                percentage = 20 + (index/len(areas)*50)
                self.progress.emit(f"Completed {index+1}/{len(areas)}", percentage)
            
            # Tambahan merge las
            self.progress.emit("Merge classification results", 70)
            print('Running Merge LAS')
            
            source_file = os.path.join(self.visual_dir, filename + '-block-' + str(test_area) + '.laz')
            destination_folder = os.path.join(self.args.output_path, "visual")
            shutil.move(source_file, destination_folder)

            las_copy = os.path.join(destination_folder, filename + '-block-' + str(test_area) + '.laz')
            out_las = os.path.join(destination_folder, filename + '_classified.laz')
            os.rename(las_copy, out_las)
            
            for (dirpath, dirnames, filenames) in os.walk(self.visual_dir):
                for inFile in filenames:
                    if inFile.endswith('.laz'):
                        in_las = os.path.join(dirpath, inFile)
                        append_to_las(in_las, out_las)
                
            shutil.move (out_las, self.args.output_path)
            print('Finished without errors - merge_LAS.py')
              
            # Record the end time
            end_time = time.time()
            
            # Calculate the elapsed time
            elapsed_time = end_time - start_time

            self.progress.emit("Remove temporary data", 95)
            shutil.rmtree(data_dir)
            shutil.rmtree(self.visual_dir)
            shutil.rmtree(os.path.join(self.args.output_path, "visual"))

            print(f"Elapsed Time: {elapsed_time} seconds")
            self.finished.emit("Finished")

        except Exception as e:
            print(f"Error : {e}")
            self.error.emit(str(e))
    
    def classification(self, filename, test_area):
        '''HYPER PARAMETER'''
        os.environ["CUDA_VISIBLE_DEVICES"] = self.args.gpu
    
        NUM_CLASSES = self.args.num_classes
        BATCH_SIZE = self.args.batch_size
        NUM_POINT = self.args.num_point

        root = os.path.join(CUR_DIR, 'data', 'sem_seg_data')

        TEST_DATASET_WHOLE_SCENE = ScannetDatasetWholeScene(root, split='test', test_area=test_area, block_points=NUM_POINT)
        
        '''MODEL LOADING'''
        classifier = dgcnn_sem_seg(self.args).cuda()
        classifier = nn.DataParallel(classifier)
        checkpoint = torch.load(self.args.model, weights_only=False)
        classifier.load_state_dict(checkpoint)
        
        classifier = classifier.eval()

        with torch.no_grad():
            scene_id = TEST_DATASET_WHOLE_SCENE.file_list
            scene_id = [x[:-4] for x in scene_id]
            
            # Edit num_batches = 1
            num_batches = 1 #len(TEST_DATASET_WHOLE_SCENE)   
            
            for batch_idx in range(num_batches):
                whole_scene_data = TEST_DATASET_WHOLE_SCENE.scene_points_list[batch_idx]
                whole_scene_label = TEST_DATASET_WHOLE_SCENE.semantic_labels_list[batch_idx]
                vote_label_pool = np.zeros((whole_scene_label.shape[0], NUM_CLASSES))            
                scene_data, scene_label, scene_smpw, scene_point_index = TEST_DATASET_WHOLE_SCENE[batch_idx]
                num_blocks = scene_data.shape[0]
                s_batch_num = (num_blocks + BATCH_SIZE - 1) // BATCH_SIZE
                # batch_data = np.zeros((BATCH_SIZE, NUM_POINT, 9)) #XYZ, RGB, NormXYZ
                
                # Add Intensity
                batch_data = np.zeros((BATCH_SIZE, NUM_POINT, 7)) #XYZ, RGB, I, NormXYZ
                
                batch_label = np.zeros((BATCH_SIZE, NUM_POINT))
                batch_point_index = np.zeros((BATCH_SIZE, NUM_POINT))
                batch_smpw = np.zeros((BATCH_SIZE, NUM_POINT))

                for sbatch in range(s_batch_num):
                    start_idx = sbatch * BATCH_SIZE
                    end_idx = min((sbatch + 1) * BATCH_SIZE, num_blocks)
                    real_batch_size = end_idx - start_idx
                    batch_data[0:real_batch_size, ...] = scene_data[start_idx:end_idx, ...]
                    batch_label[0:real_batch_size, ...] = scene_label[start_idx:end_idx, ...]
                    batch_point_index[0:real_batch_size, ...] = scene_point_index[start_idx:end_idx, ...]
                    batch_smpw[0:real_batch_size, ...] = scene_smpw[start_idx:end_idx, ...]
                    batch_data[:, :, 3] /= 1.0 # Normalize Intensity

                    torch_data = torch.Tensor(batch_data)
                    torch_data = torch_data.float().cuda()
                    torch_data = torch_data.transpose(2, 1)

                    seg_pred  = classifier(torch_data)

                    seg_pred = seg_pred.permute(0, 2, 1).contiguous()
                    pred = seg_pred.max(dim=2)[1]
                    pred_np = pred.detach().cpu().numpy()
                    
                    vote_label_pool = add_vote(vote_label_pool, batch_point_index[0:real_batch_size, ...],
                                            pred_np[0:real_batch_size, ...],
                                            batch_smpw[0:real_batch_size, ...])
                    
                    
                pred_label =  np.argmax(vote_label_pool, 1)
                
                whole_scene_data = whole_scene_data.astype(np.float64)
                
                # Change to UTM
                whole_scene_data[:, 0:2] += self.xy_min

                result_data = []
                for i in range(whole_scene_label.shape[0]):
                    data_point = [whole_scene_data[i, 0], whole_scene_data[i, 1], whole_scene_data[i, 2], whole_scene_data[i, 3], pred_label[i]]
                    result_data.append(data_point)
                
                result_data = np.array(result_data)
                        
                filename = os.path.join(self.visual_dir, filename + '-block-' + str(test_area))
                save_las(result_data, filename, isIntensity=True)
