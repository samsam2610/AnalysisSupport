
import os
import csv
from pathlib import Path
 
class VideoData:
    def __init__(self,
                 video,
                 videoProcessingStatus=False):
        self.videoName = str(Path(video).stem)
        self.videoFolder = str(Path(video).parents[0])
        self.videoProcessingStatus = videoProcessingStatus
        self.videoPath = video

class ProcessVideoList:

    def __init__(self,
                 videofile_pathList,
                 videotype='.avi',
                 fields=['Video', 'Good analysis (1 true/0 false)']):

        self.videoList = []
        self.processingData = {}
        self.fields = fields 

        for folder in videofile_pathList:
            dataFile = os.path.join(folder, "analysis-status.csv")
            self.getVideoProcessingStatus(dataFile)

            videos = self.getListOfVideos([folder], videotype)
            for video in videos:
                videoName = str(Path(video).stem)
                if videoName in self.processingData:
                    processingStatus = self.processingData[str(Path(video).stem)]
                else:
                    processingStatus = False
                    self.writeVideoProcessingStatus(dataFile, video)
                
                self.videoList.append(VideoData(video, videoProcessingStatus=processingStatus))

    def getListOfVideos(self, videos, videotype):
        if [os.path.isdir(i) for i in videos] == [True]:  # checks if input is a directory
            from random import sample

            videofolder = videos[0]

            os.chdir(videofolder)
            videolist = [
                os.path.join(videofolder, fn)
                for fn in os.listdir(os.curdir)
                if os.path.isfile(fn)
                and fn.endswith(videotype)
                and "_labeled." not in fn
                and "_full." not in fn
            ]

            Videos = sample(
                videolist, len(videolist)
            )
        else:
            if isinstance(videos, str):
                if (
                    os.path.isfile(videos)
                    and "_labeled." not in videos
                    and "_full." not in videos
                ):  # #or just one direct path!
                    Videos = [videos]
                else:
                    Videos = []
            else:
                Videos = [
                    v
                    for v in videos
                    if os.path.isfile(v)
                    and "_labeled." not in v
                    and "_full." not in v
                ]
        return Videos
    
    def getVideoProcessingStatus(self, dataFile):
        if os.path.isfile(dataFile):
            with open(dataFile, 'r') as csv_file:
                reader = csv.reader(csv_file)
                next(reader, None)
                for rows in reader:
                    if int(rows[1]) == 0:
                        status = False
                    elif int(rows[1]) == 1:
                        status = True

                    self.processingData[rows[0]] = status
        
    def writeVideoProcessingStatus(self, dataFile, video):
        with open(dataFile, 'w') as csv_file:
            csvwriter = csv.writer(csv_file)
            csvwriter.writerow(self.fields)
            videofolder = str(Path(video).parents[0])
            videoName = str(Path(video).stem)

            csvwriter.writerows([[videoName, 0]])

    def getListofUnprocessedVideos(self):
        return [self.videoList[i].videoPath for i in range(len(self.videoList)) if self.videoList[i].videoProcessingStatus == False]




                


