import os, sys, glob
from aniposelib.utils import load_pose2d_fnames

class LabelManager:
    def __init__(self, ProjectManager=None) -> None:
        for key, val in vars(ProjectManager).items():
            setattr(self, key, val)

        self.labeled_video_check = True

    def create_pose_dict(self):
        # create video dict with cam names

        videos = [
            glob.glob(os.path.join(self.videos_pair[i].replace('.avi', '') + "*" + ".h5"))
            for i in range(len(self.videos_pair))
        ]
        videos = [y for x in videos for y in x]
        self.videos_result = dict(zip(self.cgroup.get_names(), videos))

        if len(videos) == 0:
            self.labeled_video_check = False

        return self.videos_result

    def load_pose2D(self, videos_result=None):
        if videos_result is None:
            try:
                videos_result = self.videos_result
            except AttributeError:
                videos_result = self.create_pose_dict()
                self.videos_result = videos_result

        self.pose2d_fnames = load_pose2d_fnames(videos_result)
        return self.pose2d_fnames

    def analyze_pose2D(self):
        pass

