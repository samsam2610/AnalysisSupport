import os
import csv
from pathlib import Path
import glob

from anipose_support.project_manager import ProjectManager
# from project_manager import *

# from deeplabcut.utils import auxiliaryfunctions

videofile_pathlist = ['/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat i0/vids',
                       '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/12-6/vids',
                       '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/vids/11-6']
model_folder = '/Users/sam/Downloads/TWO_CAM_FOR_SAM/R11_treadmill/'

class PathManager:
    def __init__(self,
                 videofile_pathList,
                 videotype='.avi',
                 cam_names=['cam1', 'cam2'],
                 calib_name ='calib',
                 model_folder=None) -> None:
        self.projectList = []
        self.videotype = videotype
        self.cam_names = cam_names
        self.calib_names = calib_name
        self.test = 2
        if model_folder is not None:
            self.model_folder = model_folder

        print('\nInitializing project path list ...')
        for folder in videofile_pathList:         
            videos_pair, videos_tail = self.get_camerawise_videos(folder)
            videos_calib, calib_path = self.get_calib_videos(folder)
            print('\nCurrent folder: ')
            print(folder)
            print('List of calib videos: ')
            print(videos_calib)

            print('\nFinding video pairs associated with this calib videos ...')
            for idx, video in enumerate(videos_pair):
                if len(videos_calib) == 0:
                    continue

                if set(videos_calib) != set(video):
                    print('\nFound a videos pair with name: ')
                    print(videos_tail[idx])
                    currentProject = ProjectManager(folder,
                                                    cam_names=cam_names,
                                                    videos_pair=video,
                                                    videos_tail=videos_tail[idx],
                                                    videos_calib=videos_calib,
                                                    calib_path=calib_path,
                                                    video_type=self.videotype)
                    self.projectList.append(currentProject)

        print('\nTotal processing projects are: ' + str(len(self.projectList)))

    def get_projects_list(self):
        return self.projectList

    def batch_triangulate(self, over_write=True):
        print('\nTriangulating available projects ...')
        for project in self.projectList:

            print('\nStarting the triangulation process ...')
            project.process_triangulate(over_write=over_write)
            print('Done')

        print('\nTriangulation done!')

    def batch_plot_data(self):
        print('\nPlotting triangulated project ...')
        for project in self.projectList:

            print('\nPlotting ...')
            project.plot_data()
            print('Done')

        print('\nPlotting done!')

    def batch_export_data(self):
        print('\nExporting data from triangulated projects ...')
        for project in self.projectList:

            print('\nExporting data ...')
            project.export_data()
            print('Done')

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

        videotail_list = list(map(lambda x: x.replace('.avi', ''), videotail_list))
        return videospair_list, videotail_list

    def get_calib_videos(self, path, calib_foldername='calibration'):
        videos = []
        for cam_name in self.cam_names:
            current_video = glob.glob(os.path.join(path, str(cam_name + "*" + self.calib_names + "*" + self.videotype)))
            if len(current_video) > 0:
                videos.append(current_video[0])
        # videos = [
        #     glob.glob(os.path.join(path, str("*" + self.calib_names + "*" + self.videotype)))
        # ]
        # videos = [y for x in videos for y in x]

        calib_path = os.path.join(path, calib_foldername)

        if len(videos) > 0:
            import shutil

            if not os.path.exists(calib_path):
                os.makedirs(calib_path)

            if os.path.exists(calib_path):
                for calib_video in videos:
                    shutil.move(calib_video, calib_path)
        
        else:
            # videos = [
            #     glob.glob(os.path.join(calib_path, str("*" + self.calib_names + "*" + self.videotype)))
            # ]
            # videos = [y for x in videos for y in x]
            for cam_name in self.cam_names:
                current_video = glob.glob(os.path.join(calib_path, str(cam_name + "*" + self.calib_names + "*" + self.videotype)))
                if len(current_video) > 0:
                    videos.append(current_video[0])


        return videos, calib_path

    def set_model_folder(self, model_folder):
        self.model_folder = model_folder
        print('Model folder is ' + model_folder)
