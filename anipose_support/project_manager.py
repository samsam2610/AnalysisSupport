import os
import csv
from pathlib import Path
import glob
import toml

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

        'board_square_side_length': 25 #  If charuco or checkerboard, square side length mm
    },
    'manual_verification': {
        'manually_verify': False
    },
    'triangulation': {
        'ransac': False,
        'optim': False,
        'scale_smooth': 2,
        'scale_length': 2,
        'scale_length_weak': 1,
        'reproj_error_threshold': 5,
        'score_threshold': 0.8,
        'n_deriv_smooth': 3,
        'constraints': [],
        'constraints_weak': [],
        'cam_regex': 'cam([1-9])',
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
    def __init__(self, project_path, videos_pair, videos_calib, config=None) -> None:
        self.project_path = project_path
        self.videos_pair = videos_pair
        self.videos_calib = videos_calib
        self.config = self.load_config(config)
        self.process_calibration(self.config)
        _ = self.dump_config(self.config)

        self.dump_config(self.config)

    def load_config(self, fname):
        if fname is None:
            fname = 'config.toml'

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
    
    def dump_config(self, config):
        fname = 'config.toml'
        # toml_string = toml.dumps(config)
        fpath = os.path.join(self.project_path, fname)
        with open(fpath, "w") as toml_file:
            toml.dump(config, toml_file)

    def process_calibration(self, config):
        from anipose.calibrate import calibrate_all
        calibrate_all(config)
    


