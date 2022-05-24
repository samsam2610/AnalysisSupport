from analysissupport.anipose_support import *

videopath_list = ['/Volumes/GoogleDrive/My Drive/Rat/treadpose/Testbig/calibration',
                  '/Volumes/GoogleDrive/My Drive/Rat/treadpose/Testsmall/calibration']

projects_path_list = PathManager(videopath_list)
projects_list = projects_path_list.get_projects_list()
print(projects_list)

projects_path_list.batch_plot_data()
projects_path_list.batch_triangulate(over_write=False)
projects_path_list.batch_plot_data()
projects_path_list.batch_export_data()