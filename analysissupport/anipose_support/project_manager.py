import sys, os
import csv
from pathlib import Path
import cv2
from cv2 import aruco
import glob
import toml
import numpy as np
import pandas as pd
from aniposelib.boards import CharucoBoard, Checkerboard
from aniposelib.cameras import Camera, CameraGroup
from aniposelib.utils import load_pose2d_fnames

from collections import defaultdict
from matplotlib.pyplot import get_cmap
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits import mplot3d
import skvideo.io
from tqdm import tqdm, trange

DEFAULT_CONFIG = {
    'video_extension': 'avi',
    'nesting': 1,
    'calibration': {
        'animal_calibration': False,
        'calibration_init': None,
        'fisheye': False,

        'board_type': "charuco",
        'board_size': [11, 8],
        'board_marker_bits': 4,

        'board_marker_dict_number': 50, # number of markers in dictionary, if aruco/charuco

        'board_marker_length': 18.75, # length of marker side (mm)

        # If aruco, length of marker separation
        # board_marker_separation_length = 1 # mm

        'board_square_side_length': 25, #  If charuco or checkerboard, square side length mm
    },
    'manual_verification': {
        'manually_verify': False
    },
    'triangulation': {
        'ransac': False,
        'optim': True,
        'scale_smooth': 2,
        'scale_length': 2,
        'scale_length_weak': 1,
        'reproj_error_threshold': 5,
        'score_threshold': 0.8,
        'n_deriv_smooth': 3,
        'constraints': [],
        'constraints_weak': [],
        'cam_regex': "cam([1-9])",
    },
    'pipeline': {
        'videos_raw': 'videos-raw',
        'pose_2d': 'pose-2d',
        'pose_2d_filter': 'pose-2d-filtered',
        'pose_2d_projected': 'pose-2d-proj',
        'pose_3d': 'pose-3d',
        'pose_3d_filter': 'pose-3d-filtered',
        'videos_labeled_2d': 'videos-labeled',
        'videos_labeled_2d_filter': 'videos-labeled-filtered',
        'calibration_videos': 'calibration',
        'calibration_results': 'calibration',
        'videos_labeled_3d': 'videos-3d',
        'videos_labeled_3d_filter': 'videos-3d-filtered',
        'angles': 'angles',
        'summaries': 'summaries',
        'videos_combined': 'videos-combined',
        'videos_compare': 'videos-compare',
        'videos_2d_projected': 'videos-2d-proj',
    },
    'filter': {
        'enabled': False,
        'type': 'medfilt',
        'medfilt': 13,
        'offset_threshold': 25,
        'score_threshold': 0.05,
        'spline': True,
        'n_back': 5,
        'multiprocessing': False
    },
    'filter3d': {
        'enabled': False
    }
}

class ProjectManager:
    def __init__(self,
                 project_path,
                 videos_pair,
                 videos_tail,
                 videos_calib,
                 calib_path,
                 cam_names=['cam1', 'cam2'],
                 video_type='.avi',
                 model_folder=None,
                 config=None) -> None:

        self.project_path = project_path
        self.calib_path = calib_path

        self.videos_pair = videos_pair
        self.videos_calib = videos_calib
        self.videos_tail = videos_tail

        self.cam_names = cam_names
        self.videos_type = video_type
        self.model_folder = model_folder
        self.config = self.load_config(config)
        self.dump_config(self.config)

        # Handle by calibration_manager.py
        self.cgroup = self.check_calibration(self.config)

        self.pose2d_fnames = self.load_label_data()
        self.status_triangulate = False

        self.output_fname = os.path.join(self.project_path, self.videos_tail + '.csv')

    def check_calibration(self, config=None):
        # Handle by calibration_manager.py
        from analysissupport.anipose_support.calibration_manager import CalibrationManager
        calibration_object = CalibrationManager(self)
        cgroup = calibration_object.check_calibration()

        return cgroup

    def process_triangulate(self, config=None, out=None, score_threshold=0.5, over_write=True):
        # Handle by data_manager.py
        from analysissupport.anipose_support.data_manager import DataManager

        self.data_object = DataManager(self)
        self.data_object.process_triangulate(config=config, out=out, score_threshold=score_threshold, over_write=over_write)

    def plot_data(self):
        # Handle by plot_manager.py
        from analysissupport.anipose_support.plot_manager import PlotManager
        try:
            plot_object = PlotManager(self, self.data_object)
            plot_object.plot_2D()
        except AttributeError:
            print('Data is not loaded or not available. Please try again!')
            pass

    def export_data(self, output_fname=None, config=None):
        try:
            self.data_object.export_data(output_fname=output_fname, config=config)
        except AttributeError:
            from analysissupport.anipose_support.data_manager import DataManager

            self.data_object = DataManager(self)
            self.data_object.process_triangulate()
            self.data_object.export_data(output_fname=output_fname, config=config)

    def load_data(self, config=None, output_fname=None):
        try:
            self.data_object.load_data(output_fname=output_fname, config=config)
        except AttributeError:
            from analysissupport.anipose_support.data_manager import DataManager

            self.data_object = DataManager(self)
            self.data_object.load_data(output_fname=output_fname, config=config)

    def load_label_data(self):
        from analysissupport.anipose_support.label_manager import LabelManager
        self.label_object = LabelManager(self)
        self.pose2d_fnames = self.label_object.load_pose2D()

        return self.pose2d_fnames

    def dump_config(self, config):
        fname = 'config.toml'
        # toml_string = toml.dumps(config)
        fpath = os.path.join(self.project_path, fname)
        with open(fpath, "w") as toml_file:
            toml.dump(config, toml_file)

    def load_config(self, fname):
        if fname is None:
            fname = os.path.join(self.project_path, 'config.toml')

        if os.path.exists(fname):
            config = toml.load(fname)
        else:
            config = dict()

        config['path'] = self.project_path

        if 'project' not in config:
            config['project'] = os.path.basename(config['path'])

        for k, v in DEFAULT_CONFIG.items():
            if k not in config:
                config[k] = v
            elif isinstance(v, dict): # handle nested defaults
                for k2, v2 in v.items():
                    if k2 not in config[k]:
                        config[k][k2] = v2

        return config


