from anipose_support import *

videopath_list = [#'/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /sample',
                  '/Volumes/GoogleDrive/My Drive/Rat/Treadmill test /rat-e/12-6/vids']

projects_path_list = PathManager(videopath_list)
projects_list = projects_path_list.get_projects_list()
print(projects_list)

projects_path_list.batch_plot_data()
projects_path_list.batch_triangulate(over_write=False)
projects_path_list.batch_plot_data()
projects_path_list.batch_export_data()