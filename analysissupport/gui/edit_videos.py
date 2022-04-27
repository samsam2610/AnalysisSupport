import datetime
import os
import pydoc
import sys
import wx

import deeplabcut

class Edit_videos(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.createControls()
        self.bindEvents()
        self.doLayout()
        self.setProperties()

    def createControl(self):
        self.VideoFolder_Add = wx.Button(self, label='Load video folder')


    def shorten_video(self, event):
        def sweet_time_format(val):
            return str(datetime.timedelta(seconds=val))

        Videos = self.filelist
        if len(Videos) > 0:
            for video in Videos:
                deeplabcut.ShortenVideo(
                    video,
                    start=sweet_time_format(self.vstart.GetValue()),
                    stop=sweet_time_format(self.vstop.GetValue()),
                )

        else:
            print("Please select a video first!")