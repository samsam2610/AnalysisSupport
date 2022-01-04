import os
import csv
from pathlib import Path
import glob

videofile_pathlist = ['/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat i0/vids',
                       '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/12-6/vids',
                       '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/vids/11-6']

class ProjectManager:
    def __init__(self, videofile_pathList, videotype='.avi', cam_names=['cam1', 'cam2'], calib_name ='calib') -> None:
        self.videoList = []
        self.videotype = videotype
        self.cam_names = cam_names
        self.calib_names = calib_name
        self.test = 2
        for folder in videofile_pathList:
            videos = self.get_camerawise_videos(folder)
            for video in videos:
                self.videoList.append(video)

    def get_camerawise_videos(self, path):
        # Find videos only specific to the cam names
        videopair_list = []
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

        # Exclude the labeled video files
        if "." in self.videotype:
            file_to_exclude = str("labeled" + self.videotype)
        else:
            file_to_exclude = str("labeled." + self.videotype)
        pass