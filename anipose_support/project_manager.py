import os
import csv
from pathlib import Path
import glob
import toml
import numpy as np
import pandas as pd
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
                 videos_tail,
                 videos_calib,
                 calib_path,
                 config=None) -> None:

        self.project_path = project_path
        self.videos_pair = videos_pair
        self.videos_calib = videos_calib
        self.videos_tail = videos_tail
        self.calib_path = calib_path
        self.cam_names = cam_names
        self.config = self.load_config(config)
        self.dump_config(self.config)
        self.videos_result = []

        self.cgroup = self.check_calibration(self.config)

        self.create_pose_dict() # create video dict with cam names
        self.pose2d_fnames = load_pose2d_fnames(self.videos_result)
        self.status_triangulate = False

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

        calib_file = os.path.join(self.calib_path, str("calibration.toml"))

        if os.path.exists(calib_file):
            print('\nCalibration file was found. Loading calibrated file ...')
            cgroup = CameraGroup.load(calib_file)

            print('Done calibration loaded!')
        else:
            print('\nCalibration file was not found. Calibrating using available videos ...')
            board = self.get_calibration_board(config)
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

    def process_triangulate(self, config=None, out=None, score_threshold=0.5):
        if out is None:
            out = self.pose2d_fnames

        if config is None:
            config = self.config

        points = out['points']
        self.all_scores = out['scores']
        self.n_cams, self.n_frames, self.n_joints, _ = points.shape

        self.bodyparts = out['bodyparts']

        # remove points that are below threshold
        points[self.all_scores < score_threshold] = np.nan

        points_flat = points.reshape(self.n_cams, -1, 2)
        scores_flat = self.all_scores.reshape(self.n_cams, -1)

        points_3d = self.cgroup.triangulate(points_flat, progress=True)
        errors = self.cgroup.reprojection_error(points_3d, points_flat, mean=True)
        good_points = ~np.isnan(points[:, :, :, 0])
        self.all_scores[~good_points] = 2

        self.num_cams = np.sum(good_points, axis=0).astype('float')

        self.all_points_3d = points_3d.reshape(self.n_frames, self.n_joints, 3)
        self.all_errors = errors.reshape(self.n_frames, self.n_joints)
        self.all_scores[~good_points] = 2
        self.scores_3d = np.min(self.all_scores, axis=0)

        self.scores_3d[self.num_cams < 2] = np.nan
        self.all_errors[self.num_cams < 2] = np.nan
        self.num_cams[self.num_cams < 2] = np.nan
        self.M = np.identity(3)
        self.center = np.zeros(3)

        self.status_triangulate = True

        return self.all_points_3d, self.all_errors, self.bodyparts

    def plot_data(self):

        if self.status_triangulate == False:
            print('The project is not triangulated. Please run process_triangulate first!')
            return

        import matplotlib.pyplot as plt

        bodyPartIndex = 2
        plt.figure(figsize=(9.4, 6))
        plt.plot(self.all_points_3d[:, bodyPartIndex, 0])
        plt.plot(self.all_points_3d[:, bodyPartIndex, 1])
        plt.plot(self.all_points_3d[:, bodyPartIndex, 2])
        plt.xlabel("Time (frames)")
        plt.ylabel("Coordinate (mm)")
        plt.title("x, y, z coordinates of {}".format(self.bodyparts[bodyPartIndex]))
        plt.show()

    def get_calibration_board(self, config):
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

    def export_data(self, output_fname=None):
        if self.status_triangulate == False:
            print('The project is not triangulated. Please run process_triangulate first!')
            return

        if output_fname is None:
            output_fname = os.path.join(self.project_path, self.videos_tail + '.csv')

        dout = pd.DataFrame()
        for bp_num, bp in enumerate(self.bodyparts):
            for ax_num, axis in enumerate(['x', 'y', 'z']):
                dout[bp + '_' + axis] = self.all_points_3d[:, bp_num, ax_num]
            dout[bp + '_error'] = self.all_errors[:, bp_num]
            dout[bp + '_ncams'] = self.num_cams[:, bp_num]
            dout[bp + '_score'] = self.scores_3d[:, bp_num]

        for i in range(3):
            for j in range(3):
                dout['M_{}{}'.format(i, j)] = self.M[i, j]

        for i in range(3):
            dout['center_{}'.format(i)] = self.center[i]

        dout['fnum'] = np.arange(self.n_frames)

        dout.to_csv(output_fname, index=False)


    def create_pose_dict(self):
        videos = [
            glob.glob(os.path.join(self.videos_pair[i].replace('.avi', '') + "*" + ".h5"))
            for i in range(len(self.videos_pair))
        ]
        videos = [y for x in videos for y in x]
        self.videos_result = dict(zip(self.cgroup.get_names(), videos))


