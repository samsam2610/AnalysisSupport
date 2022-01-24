import os
import csv
from pathlib import Path
import glob
import toml
import numpy as np
from aniposelib.boards import CharucoBoard, Checkerboard
from aniposelib.cameras import Camera, CameraGroup
from aniposelib.utils import load_pose2d_fnames


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
                 cam_names,
                 videos_pair,
                 videos_calib,
                 calib_path,
                 config=None) -> None:

        self.project_path = project_path
        self.videos_pair = videos_pair
        self.videos_calib = videos_calib
        self.calib_path = calib_path
        self.cam_names = cam_names
        self.config = self.load_config(config)
        self.dump_config(self.config)
        self.videos_result = []

        self.cgroup = self.check_calibration(self.config)

        self.create_pose_dict() # create video dict with cam names
        self.pose2d_fnames = load_pose2d_fnames(self.videos_result, self.cam_names)

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

    def check_calibration(self, config=None):
        if config is None:
            config = self.config

        calib_file = glob.glob(os.path.join(self.calib_path, str("calibration.toml")))
        print(calib_file)
        if os.path.exists(calib_file):
            cgroup = CameraGroup.load(calib_file)
        else:
            print('Calibration file was not found. Calibrating using available videos')
            board = CharucoBoard(config)
            cgroup = CameraGroup.from_names(self.cam_names)

            error, all_rows = cgroup.calibrate_videos(self.videos_calib, board)
            cgroup.dump(calib_file)
            print('Done calibration. File saved!')

        return cgroup

    def process_calibration(self, config=None):
        if config is None:
            config = self.config

        from anipose.calibrate import calibrate_all
        try:
            calibrate_all(config)
            print('Calibration file was created')
        except Exception as e:
            print('Calibration errors')
            print(e)
            pass

    def process_triangulate(self, d=None):
        if d is None:
            d = self.pose2d_fnames

        score_threshold = 0.5

        n_cams, n_points, n_joints, _ = d['points'].shape
        points = d['points']
        scores = d['scores']

        bodyparts = d['bodyparts']

        # remove points that are below threshold
        points[scores < score_threshold] = np.nan

        points_flat = points.reshape(n_cams, -1, 2)
        scores_flat = scores.reshape(n_cams, -1)

        p3ds_flat = cgroup.triangulate(points_flat, progress=True)
        reprojerr_flat = cgroup.reprojection_error(p3ds_flat, points_flat, mean=True)

        p3ds = p3ds_flat.reshape(n_points, n_joints, 3)
        reprojerr = reprojerr_flat.reshape(n_points, n_joints)

        return p3ds, reprojerr

    def get_calibration_board(config):
        calib = config['calibration']

        board_size = calib['board_size']
        board_type = calib['board_type'].lower()

        if board_type == 'aruco':
            raise NotImplementedError("aruco board is not implemented with the current pipeline")
        elif board_type == 'charuco':
            board = CharucoBoard(
                board_size[0], board_size[1],
                calib['board_square_side_length'],
                calib['board_marker_length'],
                calib['board_marker_bits'],
                calib['board_marker_dict_number'])
        elif board_type == 'checkerboard':
            board = Checkerboard(board_size[0], board_size[1],
                                 calib['board_square_side_length'])
        else:
            raise ValueError("board_type should be one of "
                             "'aruco', 'charuco', or 'checkerboard' not '{}'".format(
                board_type))

        return board

    def create_pose_dict(self):
        videos = [
            glob.glob(os.path.join(self.videos_pair[i].replace('.avi', '') + "*" + ".h5"))
            for i in range(len(self.videos_pair))
        ]
        videos = [y for x in videos for y in x]
        self.videos_result = dict(zip(self.cam_names, videos))


