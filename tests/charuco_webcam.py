#!/usr/bin/env python

import cv2
from cv2 import aruco

import numpy as np
import toml
import matplotlib.pyplot as plt

import glob
import random
import sys, os

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

dkey = (4, 50)
aruco_dict = aruco.getPredefinedDictionary(ARUCO_DICTS[dkey])

board = cv2.aruco.CharucoBoard_create(11, 8, 25, 18.75, aruco_dict)

params = aruco.DetectorParameters_create()
params.cornerRefinementMethod = aruco.CORNER_REFINE_CONTOUR
params.adaptiveThreshWinSizeMin = 100
params.adaptiveThreshWinSizeMax = 1000
params.adaptiveThreshWinSizeStep = 50
params.adaptiveThreshConstant = 0

def read_chessboards(frames):
    """
    Charuco base pose estimation.
    """
    all_corners = []
    all_ids = []

    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=params)

        if len(corners) > 0:
            print('Succeed!')
            ret, c_corners, c_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, gray, board)
            # ret is the number of detected corners
            if ret > 0:
                all_corners.append(c_corners)
                all_ids.append(c_ids)
        else:
            print('Failed!')

    imsize = gray.shape
    return all_corners, all_ids, imsize

def draw_axis(frame, camera_matrix, dist_coeff, board, verbose=True):
    try:
        corners, ids, rejected_points = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=params)

        if corners is None or ids is None:
            print('No corner detected')
            return None
        if len(corners) != len(ids) or len(corners) == 0:
            print('Incorrect corner or no corner detected!')
            return None

        corners, ids, rejectedCorners, recoveredIdxs = cv2.aruco.refineDetectedMarkers(frame, board, corners, ids,
                                                                                       rejected_points, camera_matrix,
                                                                                       dist_coeff, parameters=params)

        if len(corners) == 0:
            return  None

        ret, c_corners, c_ids = cv2.aruco.interpolateCornersCharuco(corners, ids,
                                                                    frame, board,
                                                                    cameraMatrix=camera_matrix, distCoeffs=dist_coeff)

        if c_corners is None or c_ids is None or len(c_corners) < 5:
            print('No corner detected after interpolation!')
            return None

        n_corners = c_corners.size // 2
        reshape_corners = np.reshape(c_corners, (n_corners, 1, 2))

        ret, p_rvec, p_tvec = cv2.aruco.estimatePoseCharucoBoard(reshape_corners,
                                                                c_ids,
                                                                board,
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
        print(exc_type, fname, exc_tb.tb_lineno)
        return None

    if verbose:
        print('Translation : {0}'.format(p_tvec))
        print('Rotation    : {0}'.format(p_rvec))
        print('Distance from camera: {0} m'.format(np.linalg.norm(p_tvec)))

    return frame

def load(fname):
        master_dict = toml.load(fname)
        keys = sorted(master_dict.keys())
        items = [master_dict[k] for k in keys if k != 'metadata']
        item = items[0]
        return True,\
               np.array(item['matrix'], dtype='float64'),\
               np.array(item['distortions'], dtype='float64'), \
               np.array(item['rotation'], dtype='float64'),\
               np.array(item['translation'], dtype='float64')

def main():

    video_path = '/Volumes/GoogleDrive/My Drive/Rat/3D tests/TWO_CAM_FOR_SAM/anipose_R11_treadmill copy/session1/calibration/cam1_short.avi'
    fname = '/Volumes/GoogleDrive/My Drive/Rat/3D tests/TWO_CAM_FOR_SAM/anipose_R11_treadmill copy/session1/calibration/calibration.toml'

    # video_path = '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/12-6/vids/calibration/cam1_12-6-calib_2021-12-06_100f-11e100g1.avi'
    # fname = '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/12-6/vids/calibration/calibration.toml'
    # fname = '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/12-6/vids/calibration/fakeCalib.toml'

    ret, camera_matrix_1, dist_coeff_1, rvec_1, tvec_1 = load(fname)
    # cap = cv2.VideoCapture(video_path)
    #
    # frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # frames = np.empty((frameCount, frameHeight, frameWidth, 3), np.dtype('uint8'))
    #
    # fc = 0
    # ret = True
    #
    # while (fc < frameCount and ret):
    #     ret, frames[fc] = cap.read()
    #     fc += 1
    # #
    # cap.release()

    # all_corners, all_ids, imsize = read_chessboards(frames)
    # all_corners = [x for x in all_corners if len(x) >= 4]
    # all_ids = [x for x in all_ids if len(x) >= 4]
    # ret, camera_matrix_2, dist_coeff_2, rvec_2, tvec_2 = cv2.aruco.calibrateCameraCharuco(
    #     all_corners, all_ids, board, imsize, None, None
    # )
    #
    # print('> Camera matrix')
    # print(camera_matrix)
    # print('> Distortion coefficients')
    # print(dist_coeff)
    #
    # # Real-time axis drawing
    cap = cv2.VideoCapture(video_path)

    frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frameRate = int(cap.get(cv2.CAP_PROP_FPS))

    size = (frameWidth, frameHeight)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    result = cv2.VideoWriter("/Users/sam/Dropbox/Tresch Lab/AnalysisSupport/tests/calibration_result.avi", fourcc, frameRate, size)
    while True:
        ret, frame = cap.read()
        if ret:
            axis_frame_1 = draw_axis(frame, camera_matrix_1, dist_coeff_1, board, False)

            if axis_frame_1 is not None:
                # cv2.imshow('Frame 1', axis_frame_1)
                result.write(axis_frame_1)
            else:
                # cv2.imshow('Frame 1', frame)
                result.write(frame)
        else:
            break

    cap.release()
    result.release()

    # Closes all the frames
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()