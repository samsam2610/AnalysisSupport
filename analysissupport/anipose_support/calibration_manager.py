from analysissupport.anipose_support.project_manager import ProjectManager
import numpy as np
import sys, os
import csv
import toml
import glob
from pathlib import Path
import cv2
from cv2 import aruco
from aniposelib.boards import CharucoBoard, Checkerboard
from aniposelib.cameras import Camera, CameraGroup
from aniposelib.utils import load_pose2d_fnames

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
class CalibrationManager:
    def __init__(self, ProjectManager) -> None:
        for key, val in vars(ProjectManager).items():
            setattr(self, key, val)

        self.boardObj = self.get_calibration_board(self.config)

    def check_calibration(self):
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

    def get_calibration_board(self, config=None):
        if config is None:
            config = self.config

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
