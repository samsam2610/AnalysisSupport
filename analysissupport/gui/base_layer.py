import wx
import os

from analysissupport.gui.configurate_project import Configurate_project, Panels_control
from analysissupport.gui.widgets import BaseFrame
from analysissupport.gui.edit_videos import Edit_videos

class MainFrame(BaseFrame):
    def __init__(self):
        super(MainFrame, self).__init__("Analysis Support")
        self.panel = wx.Panel(self)
        self.nb = wx.Notebook(self.panel)

        page1 = Panels_control(self.nb, self.gui_size)
        self.nb.AddPage(page1, "Manage Project")

        page2 = Edit_videos(self.nb)
        self.nb.AddPage(page2, "Edit videos")
        
        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.nb, 1, wx.EXPAND)
        self.panel.SetSizer(self.sizer)

def launch_support():
    app = wx.App()
    frame = MainFrame().Show()
    app.MainLoop()

if __name__ == '__main__':
    app = wx.App(0)
    frame = MainFrame()
    frame.Show()
    frame.SetSize(600, 600)
    wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()