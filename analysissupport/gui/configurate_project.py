import wx
import wx.grid
import uuid
import ast
import wx.lib.inspection

DEFAULT_CONFIG = {
    'video_extension': 'avi',
    'nesting': 1,
    'calibration': {
        'animal_calibration': False,
        'calibration_init': None,
        'fisheye': False,

        'board_type': "charuco",
        'board_size': [11, 8],
        'board_marker_bits': 4,

        'board_marker_dict_number': 50, # number of markers in dictionary, if aruco/charuco

        'board_marker_length': 18.75, # length of marker side (mm)

        # If aruco, length of marker separation
        # board_marker_separation_length = 1 # mm

        'board_square_side_length': 25, #  If charuco or checkerboard, square side length mm
    },
    'manual_verification': {
        'manually_verify': False
    },
    'triangulation': {
        'ransac': False,
        'optim': True,
        'scale_smooth': 2,
        'scale_length': 2,
        'scale_length_weak': 1,
        'reproj_error_threshold': 5,
        'score_threshold': 0.8,
        'n_deriv_smooth': 3,
        'constraints': [],
        'constraints_weak': [],
        'cam_regex': "cam([1-9])",
    },
    'pipeline': {
        'videos_raw': 'videos-raw',
        'pose_2d': 'pose-2d',
        'pose_2d_filter': 'pose-2d-filtered',
        'pose_2d_projected': 'pose-2d-proj',
        'pose_3d': 'pose-3d',
        'pose_3d_filter': 'pose-3d-filtered',
        'videos_labeled_2d': 'videos-labeled',
        'videos_labeled_2d_filter': 'videos-labeled-filtered',
        'calibration_videos': 'calibration',
        'calibration_results': 'calibration',
        'videos_labeled_3d': 'videos-3d',
        'videos_labeled_3d_filter': 'videos-3d-filtered',
        'angles': 'angles',
        'summaries': 'summaries',
        'videos_combined': 'videos-combined',
        'videos_compare': 'videos-compare',
        'videos_2d_projected': 'videos-2d-proj',
    },
    'filter': {
        'enabled': False,
        'type': 'medfilt',
        'medfilt': 13,
        'offset_threshold': 25,
        'score_threshold': 0.05,
        'spline': True,
        'n_back': 5,
        'multiprocessing': False
    },
    'filter3d': {
        'enabled': False
    }
}

class Panels_control(wx.Panel):

    def __init__(self, parent, gui_size):
        self.parent = parent
        h = gui_size[0]
        w = gui_size[1]
        wx.Panel.__init__(self, parent, -1, style=wx.SUNKEN_BORDER, size=(h, w))
        self.config = DEFAULT_CONFIG
        self.createControls()
        self.bindEvents()
        self.doLayout()
        self.setProperties()

    def createControls(self):
        self.logger = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        # Anipose config default load and display
        self.APconfig_label = wx.StaticText(self, label='Anipose config')
        self.APconfig_display = wx.grid.Grid(self, size=(200, 200))
        self.default_APconfig_Load = wx.Button(self, label='Load default')
        self.APconfig_Load = wx.Button(self, label='Load config')
        self.APconfig_Save = wx.Button(self, label='Save config')

        # DLC config path load and write
        self.path_DLCconfig_label = wx.StaticText(self, label="Config path")
        self.path_DLCconfig_control = wx.TextCtrl(self, value="DLC config path here")
        self.path_DLCconfig_Add = wx.Button(self, label="Add config")
        self.path_DLCconfig_Browse = wx.Button(self, label="Browse path")

    def bindEvents(self):
        for control, event, handler in \
                [
                    (self.path_DLCconfig_control, wx.EVT_TEXT, self.on_path_DLCConfig_entered),
                    (self.path_DLCconfig_Browse, wx.EVT_BUTTON, self.on_pathDLC_Browse),
                    (self.path_DLCconfig_Add, wx.EVT_BUTTON, self.on_path_DLCConfig_Add)
                ]:
            control.Bind(event, handler)

        for control, event, handler in \
                [
                    (self.default_APconfig_Load, wx.EVT_BUTTON, self.on_APconfig_default_load),
                    (self.APconfig_Load, wx.EVT_BUTTON, self.on_APconfig_load),
                    (self.APconfig_Save, wx.EVT_BUTTON, self.on_APconfig_save)
                ]:
            control.Bind(event, handler)

        for control, event, handler in \
                [
                    (self.APconfig_display, wx.grid.EVT_GRID_SELECT_CELL, self.on_APconfig_selected),
                    (self.APconfig_display, wx.grid.EVT_GRID_CELL_CHANGING, self.on_APconfig_changing)
                ]:
            control.Bind(event, handler)

    def setProperties(self):
        i = self.getConfigLen(DEFAULT_CONFIG)

        self.APconfig_display.CreateGrid(i, 4)
        self.APconfig_display.SetSelectionMode(wx.grid.Grid.SelectRows)
        self.APconfig_display.SetRowLabelSize(30)
        self.APconfig_display.SetColLabelValue(0, "Parameter")
        self.APconfig_display.SetColSize(0, 100)
        self.APconfig_display.SetColLabelValue(1, "Group")
        self.APconfig_display.SetColSize(1, 50)
        self.APconfig_display.SetColLabelValue(2, "Value")
        self.APconfig_display.SetColSize(2, 50)
        self.APconfig_display.SetColLabelValue(3, "Value type")
        self.APconfig_display.SetColSize(2, 50)

    def doLayout(self):
        ''' Layout the controls that were created by createControls().
            Form.doLayout() will raise a NotImplementedError because it
            is the responsibility of subclasses to layout the controls. '''
        raise NotImplementedError

        # Callback methods:
    def on_APconfig_save(self, event):
        print("Hello")
        num_rows = self.APconfig_display.GetNumberRows()
        for index_row in range(0, num_rows):
            current_Type = self.APconfig_display.GetCellValue(index_row, 3)
            current_key_1 = self.APconfig_display.GetCellValue(index_row, 0)
            current_key_2 = self.APconfig_display.GetCellValue(index_row, 1)
            current_value = self.APconfig_display.GetCellValue(index_row, 2)
            if not current_key_2.strip():
                self.config[current_key_1] = self.tryeval(current_value, current_Type)
            else:
                self.config[current_key_2][current_key_1] = self.tryeval(current_value, current_Type)

        # Check config
        for key_1, value_1 in self.config.items():
            if not isinstance(value_1, dict):
                print(key_1, "->", value_1)
            else:
                for key_2, value_2 in value_1.items():
                    print(key_2, "->", value_2)



    def tryeval(self, val, type):
        try:
            val = ast.literal_eval(val)
        except ValueError:
            pass
        except SyntaxError:
            if type is "str":
                return val
        return val

    def on_APconfig_changing(self, event):
        self.refresh_APconfig_display()

    def getConfigLen(self, config: dict):
        i = 0
        for key_1, value_1 in config.items():
            if not isinstance(value_1, dict):
                i += 1
            else:
                for key_2, value_2 in value_1.items():
                    i += 1

        return i

    def refresh_APconfig_display(self):
        self.APconfig_display.ClearGrid()
        if (self.APconfig_display.GetNumberRows() < self.getConfigLen(self.config)):
            diff_row = self.getConfigLen(self.config) - self.APconfig_display.GetNumberRows()
            self.APconfig_display.AppendRows(numRows=diff_row)
        i = 0
        for key_1, value_1 in self.config.items():
            if not isinstance(value_1, dict):
                print(key_1, "->", value_1)
                self.APconfig_display.SetCellValue(i, 0, str(key_1))
                self.APconfig_display.SetCellValue(i, 2, str(value_1))
                self.APconfig_display.SetCellValue(i, 3, type(value_1).__name__)
                i += 1
            else:
                for key_2, value_2 in value_1.items():
                    print(key_2, "->", value_2)
                    self.APconfig_display.SetCellValue(i, 0, str(key_2))
                    self.APconfig_display.SetCellValue(i, 1, str(key_1))
                    self.APconfig_display.SetCellValue(i, 2, str(value_2))
                    self.APconfig_display.SetCellValue(i, 3, type(value_2).__name__)
                    i += 1

    def on_APconfig_selected(self, event):
        pass

    def on_APconfig_default_load(self, event):
        self.config = DEFAULT_CONFIG

    def on_APconfig_load(self, event):
        self.refresh_APconfig_display()

    def on_path_DLCConfig_entered(self, event):
        self.__log('The path to DLC config is: %s' % event.GetString())
        self.path_DLCconfig_control.Value = event.GetString()

    def on_path_DLCConfig_Add(self, event):
        self.config['model_folder'] = self.path_DLCconfig_control.Value
        self.refresh_APconfig_display()
        self.APconfig_display.AppendRows()

    def on_pathDLC_Browse(self, event):
        with wx.FileDialog(self, "Select the model config file", wildcard="*.yaml",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()

            try:
                self.path_DLCconfig_control.Value = pathname
                self.config["model_folder"] = pathname

            except IOError:
                wx.LogError("Cannot open file")

    # Helper method(s):

    def __log(self, message):
        ''' Private method to append a string to the logger text
            control. '''
        self.logger.AppendText('%s\n' % message)

    def doLayout(self):
        ''' Layout the controls by means of sizers. '''

        # A horizontal BoxSizer will contain the GridSizer (on the left)
        # and the logger text control (on the right):
        boxSizer_main = wx.BoxSizer(orient=wx.HORIZONTAL)
        boxSizer_configData = wx.BoxSizer(orient=wx.HORIZONTAL)

        # Prepare some reusable arguments for calling sizer.Add():
        expandOption = dict(flag=wx.EXPAND)
        noOptions = dict()
        emptySpace = ((0, 0), noOptions)

        DLCpath_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        for control, options in \
                [
                    (self.path_DLCconfig_label, dict(flag=wx.ALIGN_CENTER)),
                    (self.path_DLCconfig_control, dict(flag=wx.ALIGN_CENTER)),
                ]:
            DLCpath_sizer.Add(control, **options)

        DLCcontrol_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        for control, options in \
                [
                    (self.path_DLCconfig_Browse, dict(border=5, flag=wx.ALIGN_CENTER)),
                    (self.path_DLCconfig_Add, dict(border=5, flag=wx.ALIGN_CENTER)),
                ]:
            DLCcontrol_sizer.Add(control, **options)

        static_DLCconfigData = wx.StaticBox(self, -1, "1 - Load DLC config data")
        staticSizer_DLCconfigData = wx.StaticBoxSizer(static_DLCconfigData, wx.VERTICAL)
        for control, options in \
                [
                    (DLCpath_sizer, dict(border=5, flag=wx.ALL | wx.EXPAND, proportion=1)),
                    (DLCcontrol_sizer, dict(border=5, flag=wx.ALL | wx.EXPAND, proportion=1))
                ]:
            staticSizer_DLCconfigData.Add(control, **options)

        ## Anipose controller
        # Add the controls to the sizers:
        ANPcontrol_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        for control, options in \
                [
                     (self.APconfig_label, noOptions),
                     (self.default_APconfig_Load, dict(flag=wx.ALIGN_CENTER)),
                     (self.APconfig_Load, dict(flag=wx.ALIGN_CENTER)),
                     (self.APconfig_Save, dict(flag=wx.ALIGN_CENTER)),
                 ]:
            ANPcontrol_sizer.Add(control, **options)

        ANPdisplay_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        for control, options in \
                [
                    (self.APconfig_display, dict(border=1, flag=wx.EXPAND, proportion=1)),
                ]:
            ANPdisplay_sizer.Add(control, **options)


        static_ANPconfigData = wx.StaticBox(self, 0,  "2 - Prepare ANP Config data")
        staticSizer_ANPconfigData = wx.StaticBoxSizer(static_ANPconfigData, wx.VERTICAL)
        for control, options in \
                [
                    (ANPcontrol_sizer, dict(border=5, proportion=0)),
                    (ANPdisplay_sizer, dict(border=5, flag=wx.ALL | wx.EXPAND, proportion=1))
                ]:
            staticSizer_ANPconfigData.Add(control, **options)

        for control, options in \
                [
                    (staticSizer_DLCconfigData, dict(border=5, flag=wx.ALL)),
                    (staticSizer_ANPconfigData, dict(border=5, flag=wx.ALL | wx.EXPAND, proportion=1)),
                    # (boxSizer_configData, dict(border=5, flag=wx.ALL)),
                    (self.logger, dict(border=5, flag=wx.ALL | wx.EXPAND, proportion=1))
                ]:
            boxSizer_main.Add(control, **options)

        self.SetSizerAndFit(boxSizer_main)


class Configurate_project(wx.Frame):
    def __init__(self, *args, **kwargs):
        # super(Configurate_project, self).__init__(*args, **kwargs)
        notebook = wx.Notebook(self)
        form1 = Panels_layout(notebook)
        notebook.AddPage(form1, 'Deep lab cut control')

        self.SetClientSize(notebook.GetBestSize())


# if __name__ == '__main__':
#     app = wx.App(0)
#     frame = Configurate_project(None, title='DLC pipeline')
#     frame.Show()
#     frame.SetSize(600, 600)
#     wx.lib.inspection.InspectionTool().Show()
#     app.MainLoop()