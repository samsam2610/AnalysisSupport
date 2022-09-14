from analysissupport.common import make_process_fun
import os

def generate_session(config, session_path, repeat=1):
    pipeline_calibration_videos = config['pipeline']['calibration_videos']
    pipeline_video_raws = config['pipeline']['videos_raw']
    pipeline_pose_2d = config['pipeline']['pose_2d']
    for repeat_time in range(repeat):
        session_name = 'Session ' + str(repeat_time + 1)
        session_path = os.path.join(session_path, session_name)
        folders = [pipeline_calibration_videos, pipeline_video_raws, pipeline_pose_2d]
        for folder in folders:
            os.makedirs(os.path.join(session_path, folder))

generate_template = make_process_fun(generate_session)