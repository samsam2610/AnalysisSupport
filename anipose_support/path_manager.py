import os
import csv
from pathlib import Path
import glob

from anipose_support.project_manager import ProjectManager
# from project_manager import *

videofile_pathlist = ['/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat i0/vids',
                       '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/12-6/vids',
                       '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/vids/11-6']

class PathManager:
    def __init__(self, videofile_pathList, videotype='.avi', cam_names=['cam1', 'cam2'], calib_name ='calib') -> None:
        self.projectList = []
        self.videotype = videotype
        self.cam_names = cam_names
        self.calib_names = calib_name
        self.test = 2

        print('\nInitializing project path list ...')
        for folder in videofile_pathList:         
            videos = self.get_camerawise_videos(folder)
            videos_calib, calib_path = self.get_calib_videos(folder)
            print('\nCurrent folder: ')
            print(folder)
            print('List of calib videos: ')
            print(videos_calib)
            for video in videos:
                if len(videos_calib) == 0:
                    pass

                if set(videos_calib) != set(video):
                    currentProject = ProjectManager(folder,
                                                    cam_names=cam_names,
                                                    videos_pair=video,
                                                    videos_calib=videos_calib,
                                                    calib_path=calib_path)
                    self.projectList.append(currentProject)

            print('\nA project was found and added!')

        print('\nTotal processing projects are: ' + str(len(self.projectList)))
    def get_camerawise_videos(self, path):
        # Find videos only specific to the cam names
        videos = [
            glob.glob(os.path.join(path, str(self.cam_names[i] + "*" + self.videotype)))
            for i in range(len(self.cam_names))
        ]
        videos = [y for x in videos for y in x]

        videomatch_list = videos.copy()
        videomatch_list = list(map(lambda x: x.replace(self.cam_names[0],'').replace(self.cam_names[1],''), videomatch_list))
        videotail_list = {x for x in videomatch_list if videomatch_list.count(x) > 1}
        videotail_list = [os.path.basename(x) for x in videotail_list]

        videospair_list = [
            [os.path.join(path, str(self.cam_names[i] + videotail_list[x]))
            for i in range(len(self.cam_names))]
            for x in range(len(videotail_list))
        ]

        return videospair_list

    def get_calib_videos(self, path, calib_foldername='calibration'):
        videos = [
            glob.glob(os.path.join(path, str("*" + self.calib_names + "*" + self.videotype)))
        ]
        videos = [y for x in videos for y in x]

        calib_path = os.path.join(path, calib_foldername)

        if len(videos) > 0:
            import shutil

            if not os.path.exists(calib_path):
                os.makedirs(calib_path)

            if os.path.exists(calib_path):
                for calib_video in videos:
                    shutil.move(calib_video, calib_path)
        
        else:
            videos = [
                glob.glob(os.path.join(calib_path, str("*" + self.calib_names + "*" + self.videotype)))
            ]
            videos = [y for x in videos for y in x]

        return videos, calib_path
