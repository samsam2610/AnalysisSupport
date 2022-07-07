#!/usr/bin/env python3
"""
DeepLabCut2.0 Toolbox (deeplabcut.org)
© A. & M. Mathis Labs
https://github.com/AlexEMG/DeepLabCut
Please see AUTHORS for contributors.

https://github.com/AlexEMG/DeepLabCut/blob/master/AUTHORS
Licensed under GNU Lesser General Public License v3.0
"""
import cv2
import datetime
import numpy as np
import os
import subprocess
import warnings


class VideoReader:
    def __init__(self, video_path):
        if not os.path.isfile(video_path):
            raise ValueError(f'Video path "{video_path}" does not point to a file.')
        self.video_path = video_path
        self.video = cv2.VideoCapture(video_path)
        if not self.video.isOpened():
            raise IOError("Video could not be opened; it may be corrupted.")
        self.parse_metadata()
        self._bbox = 0, 1, 0, 1
        self._n_frames_robust = None

    def __repr__(self):
        string = "Video (duration={:0.2f}, fps={}, dimensions={}x{})"
        return string.format(self.calc_duration(), self.fps, *self.dimensions)

    def __len__(self):
        return self._n_frames

    def check_integrity(self):
        dest = os.path.join(self.directory, f"{self.name}.log")
        command = f"ffmpeg -v error -i {self.video_path} -f null - 2>{dest}"
        subprocess.call(command, shell=True)
        if os.path.getsize(dest) != 0:
            warnings.warn(f'Video contains errors. See "{dest}" for a detailed report.')

    def check_integrity_robust(self):
        numframes = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        fr = 0
        while fr < numframes:
            success, frame = self.video.read()
            if not success or frame is None:
                warnings.warn(f'Opencv failed to load frame {fr}. Use ffmpeg to re-encode video file')
            fr += 1

    @property
    def name(self):
        return os.path.splitext(os.path.split(self.video_path)[1])[0]

    @property
    def format(self):
        return os.path.splitext(self.video_path)[1]

    @property
    def directory(self):
        return os.path.dirname(self.video_path)

    @property
    def metadata(self):
        return dict(
            n_frames=len(self), fps=self.fps, width=self.width, height=self.height
        )

    def get_n_frames(self, robust=False):
        if not robust:
            return self._n_frames
        elif not self._n_frames_robust:
            command = (
                f'ffprobe -i "{self.video_path}" -v error -count_frames '
                f"-select_streams v:0 -show_entries stream=nb_read_frames "
                f"-of default=nokey=1:noprint_wrappers=1"
            )
            output = subprocess.check_output(
                command, shell=True, stderr=subprocess.STDOUT
            )
            self._n_frames_robust = int(output)
        return self._n_frames_robust

    def calc_duration(self, robust=False):
        if robust:
            command = (
                f'ffprobe -i "{self.video_path}" -show_entries '
                f'format=duration -v quiet -of csv="p=0"'
            )
            output = subprocess.check_output(
                command, shell=True, stderr=subprocess.STDOUT
            )
            return float(output)
        return len(self) / self.fps

    def set_to_frame(self, ind):
        if ind < 0:
            raise ValueError("Index must be a positive integer.")
        last_frame = len(self) - 1
        if ind > last_frame:
            warnings.warn(
                "Index exceeds the total number of frames. "
                "Setting to last frame instead."
            )
            ind = last_frame
        self.video.set(cv2.CAP_PROP_POS_FRAMES, ind)

    def reset(self):
        self.set_to_frame(0)

    def read_frame(self, shrink=1, crop=False):
        success, frame = self.video.read()
        if not success:
            return
        frame = frame[..., ::-1]  # return RGB rather than BGR!
        if crop:
            x1, x2, y1, y2 = self.get_bbox(relative=False)
            frame = frame[y1:y2, x1:x2]
        if shrink > 1:
            h, w = frame.shape[:2]
            frame = cv2.resize(
                frame,
                (w // shrink, h // shrink),
                fx=0,
                fy=0,
                interpolation=cv2.INTER_AREA,
            )
        return frame

    def get_bbox(self, relative=False):
        x1, x2, y1, y2 = self._bbox
        if not relative:
            x1 = int(self._width * x1)
            x2 = int(self._width * x2)
            y1 = int(self._height * y1)
            y2 = int(self._height * y2)
        return x1, x2, y1, y2

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, fps):
        if not fps > 0:
            raise ValueError("Frame rate should be positive.")
        self._fps = fps

    @property
    def width(self):
        x1, x2, _, _ = self.get_bbox(relative=False)
        return x2 - x1

    @property
    def height(self):
        _, _, y1, y2 = self.get_bbox(relative=False)
        return y2 - y1

    @property
    def dimensions(self):
        return self.width, self.height

    def parse_metadata(self):
        self._n_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        if self._n_frames >= 1e9:
            warnings.warn(
                "The video has more than 10^9 frames, we recommend chopping it up."
            )
        self._width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = round(self.video.get(cv2.CAP_PROP_FPS), 2)

    def close(self):
        self.video.release()
