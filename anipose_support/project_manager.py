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
ARUCO_DICTS = {
    (4, 50): aruco.DICT_4X4_50,
    (5, 50): aruco.DICT_5X5_50,
    (6, 50): aruco.DICT_6X6_50,
    (7, 50): aruco.DICT_7X7_50,
    (4, 100): aruco.DICT_4X4_100,
    (5, 100): aruco.DICT_5X5_100,
    (6, 100): aruco.DICT_6X6_100,
    (7, 100): aruco.DICT_7X7_100,
    (4, 250): aruco.DICT_4X4_250,
    (5, 250): aruco.DICT_5X5_250,
    (6, 250): aruco.DICT_6X6_250,
    (7, 250): aruco.DICT_7X7_250,
    (4, 1000): aruco.DICT_4X4_1000,
    (5, 1000): aruco.DICT_5X5_1000,
    (6, 1000): aruco.DICT_6X6_1000,
    (7, 1000): aruco.DICT_7X7_1000
}

params = aruco.DetectorParameters_create()
params.cornerRefinementMethod = aruco.CORNER_REFINE_CONTOUR
params.adaptiveThreshWinSizeMin = 100
params.adaptiveThreshWinSizeMax = 700
params.adaptiveThreshWinSizeStep = 50
params.adaptiveThreshConstant = 0


def connect(ax, points, bps, bp_dict, color):
    ixs = [bp_dict[bp] for bp in bps]
    # return mlab.plot3d(points[ixs, 0], points[ixs, 1], points[ixs, 2],
    #                    np.ones(len(ixs)), reset_zoom=False,
    #                    color=color, tube_radius=None, line_width=10)
    return ax.plot3D(points[ixs, 0], points[ixs, 1], points[ixs, 2])


def connect_all(ax, points, scheme, bp_dict, cmap):
    lines = []
    for i, bps in enumerate(scheme):
        line = connect(ax, points, bps, bp_dict, color=cmap(i)[:3])
        lines.append(line)
    return lines


def update_line(line, points, bps, bp_dict):
    ixs = [bp_dict[bp] for bp in bps]
    # ixs = [bodyparts.index(bp) for bp in bps]
    new = np.vstack([points[ixs, 0], points[ixs, 1], points[ixs, 2]]).T
    line.mlab_source.points = new


def update_all_lines(lines, points, scheme, bp_dict):
    for line, bps in zip(lines, scheme):
        update_line(line, points, bps, bp_dict)


def update(framenum, framedict, all_points, scheme, bp_dict, cmap, ax, low, high):
    ax.clear()
    nparts = len(bp_dict)
    if framenum in framedict:
        points = all_points[:, framenum]
    else:
        points = np.ones((nparts, 3))*np.nan

    ax.axes.set_xlim3d(left=low[0], right=high[0])
    ax.axes.set_ylim3d(bottom=low[1], top=high[1])
    ax.axes.set_zlim3d(bottom=low[2], top=high[2])
    connect_all(ax, points, scheme, bp_dict, cmap)
    return ax


class ProjectManager:
    def __init__(self,
                 project_path,
                 videos_pair,
                 videos_tail,
                 videos_calib,
                 calib_path,
                 cam_names=['cam1', 'cam2'],
                 video_type='.avi',
                 config=None) -> None:

        self.project_path = project_path
        self.calib_path = calib_path

        self.videos_pair = videos_pair
        self.videos_calib = videos_calib
        self.videos_tail = videos_tail

        self.cam_names = cam_names
        self.videos_type = video_type
        self.config = self.load_config(config)
        self.dump_config(self.config)
        self.videos_result = []

        self.boardObj = self.get_calibration_board(self.config)
        self.cgroup = self.check_calibration(self.config)


        self.create_pose_dict() # create video dict with cam names
        self.pose2d_fnames = load_pose2d_fnames(self.videos_result)
        self.status_triangulate = False

        self.output_fname = os.path.join(self.project_path, self.videos_tail + '.csv')

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
            print(self.cam_names)
            cgroup = CameraGroup.from_names(self.cam_names)
            videos_calib = [[i] for i in self.videos_calib]
            error, all_rows = cgroup.calibrate_videos(videos=videos_calib, board=self.boardObj)
            cgroup.dump(calib_file)
            print('Done calibration. File saved!')

        print('\n Labeling calibration video ...')
        self.label_calib_videos(calib_file=calib_file)
        print('Done labeling!')

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

    def process_triangulate(self, config=None, out=None, score_threshold=0.5, over_write=True):
        if out is None:
            out = self.pose2d_fnames

        if config is None:
            config = self.config

        if os.path.exists(self.output_fname):
            print('\nThe videos were triangulate before ...')
            if not over_write:
                print('To re-do the process, please try again with overwriting permission!')
                self.status_triangulate = True
                print('Loading the processed data ...')
                self.load_data()
                print('Finished loading data!')
                return
            else:
                print('Re-triangulating ...')

        points = out['points']
        self.all_scores = out['scores']
        self.n_cams, self.n_frames, self.n_joints, _ = points.shape

        self.body_parts = out['bodyparts']

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

        self.optim_data(config=config)

        self.status_triangulate = True

        return self.all_points_3d, self.all_errors, self.body_parts

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
        plt.title("x, y, z coordinates of {}".format(self.body_parts[bodyPartIndex]))
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

    def export_data(self, output_fname=None, config=None):
        if self.status_triangulate == False:
            print('The project is not triangulated. Please run process_triangulate first!')
            return

        if output_fname is None:
            output_fname = os.path.join(self.project_path, self.videos_tail + '.csv')

        if config is None:
            config = self.config

        dout = pd.DataFrame()
        for bp_num, bp in enumerate(self.body_parts):
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

    def load_data(self, config=None, output_fname=None):
        if output_fname is None:
            output_fname = self.output_fname

        if config is None:
            config = self.config

        try:
            scheme = config['labeling']['scheme']
        except KeyError:
            scheme = []
            
        data = pd.read_csv(output_fname)
        cols = [x for x in data.columns if '_error' in x]

        if len(scheme) == 0:
            self.body_parts = [c.replace('_error', '') for c in cols]
        else:
            self.body_parts = sorted(set([x for dx in scheme for x in dx]))

        bp_dict = dict(zip(self.body_parts, range(len(self.body_parts))))

        self.all_points_3d = np.transpose(np.array([np.array(data.loc[:, (bp + '_x', bp + '_y', bp + '_z')])
                                    for bp in self.body_parts], dtype='float64'), [1, 0, 2])

        self.all_errors = np.transpose(np.array([np.array(data.loc[:, bp + '_error'])
                                        for bp in self.body_parts], dtype='float64'), [1, 0])

        self.scores_3d = np.transpose(np.array([np.array(data.loc[:, bp + '_score'])
                                        for bp in self.body_parts], dtype='float64'), [1, 0])

        self.num_cams = np.transpose(np.array([np.array(data.loc[:, bp + '_ncams'])
                                        for bp in self.body_parts], dtype='float64'), [1, 0])
        self.M = np.zeros((3,3))
        for i in range(3):
            for j in range(3):
                self.M[i, j] = data.loc[0, 'M_{}{}'.format(i, j)]

        self.center = np.zeros(3)
        for i in range(3):
             self.center[i] = data.loc[0, 'center_{}'.format(i)]

        self.n_frames = np.max(data.loc[:, 'fnum']) + 1
        self.optim_data(config=config)

    def create_pose_dict(self):
        videos = [
            glob.glob(os.path.join(self.videos_pair[i].replace('.avi', '') + "*" + ".h5"))
            for i in range(len(self.videos_pair))
        ]
        videos = [y for x in videos for y in x]
        self.videos_result = dict(zip(self.cgroup.get_names(), videos))

    def draw_axis(self, frame, camera_matrix, dist_coeff, boardObj=None, verbose=True):
        if boardObj is None:
            boardObj = self.boardObj

        try:
            corners, ids, rejected_points = cv2.aruco.detectMarkers(frame, boardObj.dictionary, parameters=params)

            if corners is None or ids is None:
                print('No corner detected')
                return None
            if len(corners) != len(ids) or len(corners) == 0:
                print('Incorrect corner or no corner detected!')
                return None

            corners, ids, rejectedCorners, recoveredIdxs = cv2.aruco.refineDetectedMarkers(frame, boardObj.board, corners, ids,
                                                                                           rejected_points,
                                                                                           camera_matrix,
                                                                                           dist_coeff,
                                                                                           parameters=params)

            if len(corners) == 0:
                return None

            ret, c_corners, c_ids = cv2.aruco.interpolateCornersCharuco(corners, ids,
                                                                        frame, boardObj.board,
                                                                        cameraMatrix=camera_matrix,
                                                                        distCoeffs=dist_coeff)

            if c_corners is None or c_ids is None or len(c_corners) < 5:
                print('No corner detected after interpolation!')
                return None

            n_corners = c_corners.size // 2
            reshape_corners = np.reshape(c_corners, (n_corners, 1, 2))

            ret, p_rvec, p_tvec = cv2.aruco.estimatePoseCharucoBoard(reshape_corners,
                                                                     c_ids,
                                                                     boardObj.board,
                                                                     camera_matrix,
                                                                     dist_coeff)

            if p_rvec is None or p_tvec is None:
                print('Cant detect rotation!')
                return None
            if np.isnan(p_rvec).any() or np.isnan(p_tvec).any():
                print('Rotation is not usable')
                return None

            cv2.aruco.drawAxis(image=frame, cameraMatrix=camera_matrix, distCoeffs=dist_coeff,
                               rvec=p_rvec, tvec=p_tvec, length=20)

            cv2.aruco.drawDetectedCornersCharuco(frame, reshape_corners, c_ids)
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            # cv2.aruco.drawDetectedMarkers(frame, rejected_points, borderColor=(100, 0, 240))

        except cv2.error as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, e)
            return None

        if verbose:
            print('Translation : {0}'.format(p_tvec))
            print('Rotation    : {0}'.format(p_rvec))
            print('Distance from camera: {0} m'.format(np.linalg.norm(p_tvec)))

        return frame

    def visualize_labels(self, config=None):
        nparts = len(bodyparts)
        framedict = dict(zip(data['fnum'], data.index))

        writer = skvideo.io.FFmpegWriter(outname, inputdict={
            # '-hwaccel': 'auto',
            '-framerate': str(fps),
        }, outputdict={
            '-vcodec': 'h264', '-qp': '28', '-pix_fmt': 'yuv420p'
        })

        cmap = get_cmap('tab10')

        points = np.copy(all_points[:, 20])
        points[0] = low
        points[1] = high

        # print(points.shape)
        s = np.arange(points.shape[0])
        good = ~np.isnan(points[:, 0])

        # fig = mlab.figure(bgcolor=(1,1,1), size=(500,500))
        # fig.scene.anti_aliasing_frames = 2

        fig = plt.figure()
        ax = plt.axes(projection='3d')

    def load_calibration(self, fname, cam_num=0):
        master_dict = toml.load(fname)
        keys = sorted(master_dict.keys())
        items = [master_dict[k] for k in keys if k != 'metadata']
        item = items[cam_num]
        return True, \
               np.array(item['matrix'], dtype='float64'), \
               np.array(item['distortions'], dtype='float64'), \
               np.array(item['rotation'], dtype='float64'), \
               np.array(item['translation'], dtype='float64')

    def label_calib_videos(self, calib_file):
        for cam_name in self.cam_names:
            cam_num = int(cam_name[3:]) - 1
            calib_vid = glob.glob(os.path.join(self.calib_path, str(cam_name + "*" + self.videos_type)))
            calib_vid = calib_vid[0]
            calib_label = os.path.join(self.calib_path, str(cam_name + "_calib_labeled" + self.videos_type))

            if os.path.exists(calib_label):
                print('Labeled calibration video found! Skipping this step ...')
                continue

            ret, camera_matrix, dist_coeff, rotation_vec, translation_vec = self.load_calibration(calib_file,
                                                                                                  cam_num=cam_num)

            cap = cv2.VideoCapture(calib_vid)

            frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frameRate = int(cap.get(cv2.CAP_PROP_FPS))

            size = (frameWidth, frameHeight)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            result = cv2.VideoWriter(calib_label,
                                     fourcc, frameRate, size)
            while True:
                ret, frame = cap.read()
                if ret:
                    axis_frame = self.draw_axis(frame, camera_matrix, dist_coeff, self.boardObj, False)

                    if axis_frame is not None:
                        result.write(axis_frame)
                    else:
                        result.write(frame)
                else:
                    break

            cap.release()
            result.release()

            # Closes all the frames
            cv2.destroyAllWindows()

    def dump_config(self, config):
        fname = 'config.toml'
        # toml_string = toml.dumps(config)
        fpath = os.path.join(self.project_path, fname)
        with open(fpath, "w") as toml_file:
            toml.dump(config, toml_file)

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

    def optim_data(self, config=None):
        if config is None:
            config = self.config

        if config['triangulation']['optim']:
            self.all_errors[np.isnan(self.all_errors)] = 0
        else:
            self.all_errors[np.isnan(self.all_errors)] = 10000
        good = (self.all_errors < 100)
        self.all_points_3d[~good] = np.nan

        self.all_points_flat = self.all_points_3d.reshape(-1, 3)
        check = ~np.isnan(self.all_points_flat[:, 0])

        if np.sum(check) < 10:
            print('too few points to plot, skipping...')
            return

        self.low_points, self.high_points = np.percentile(self.all_points_flat[check], [1, 99], axis=0)


