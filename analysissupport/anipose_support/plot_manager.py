from analysissupport.anipose_support.project_manager import ProjectManager
import numpy as np


class PlotManager:
    def __init__(self, ProjectManager=None, DataManager=None) -> None:
        for key, val in vars(ProjectManager).items():
            setattr(self, key, val)
        for key, val in vars(DataManager).items():
            setattr(self, key, val)

    def plot_2D(self):

        if self.status_triangulate == False:
            print('The project is not triangulated. Please run process_triangulate first!')
            return

        import matplotlib.pyplot as plt

        bodyPartIndex = 2
        plt.figure(figsize=(9.4, 6))
        plt.plot(self.all_points_3d[:, bodyPartIndex, 0])
        plt.plot(self.all_points_3d[:, bodyPartIndex, 1])
        plt.plot(self.all_points_3d[:, bodyPartIndex, 2])
        plt.xlabel("Time (frames)")
        plt.ylabel("Coordinate (mm)")
        plt.title("x, y, z coordinates of {}".format(self.body_parts[bodyPartIndex]))
        plt.show()


    def connect(ax, points, bps, bp_dict, color):
        ixs = [bp_dict[bp] for bp in bps]
        # return mlab.plot3d(points[ixs, 0], points[ixs, 1], points[ixs, 2],
        #                    np.ones(len(ixs)), reset_zoom=False,
        #                    color=color, tube_radius=None, line_width=10)
        return ax.plot3D(points[ixs, 0], points[ixs, 1], points[ixs, 2])

    def connect_all(self, ax, points, scheme, bp_dict, cmap):
        lines = []
        for i, bps in enumerate(scheme):
            line = self.connect(ax, points, bps, bp_dict, color=cmap(i)[:3])
            lines.append(line)
        return lines

    def update_line(self, line, points, bps, bp_dict):
        ixs = [bp_dict[bp] for bp in bps]
        # ixs = [bodyparts.index(bp) for bp in bps]
        new = np.vstack([points[ixs, 0], points[ixs, 1], points[ixs, 2]]).T
        line.mlab_source.points = new

    def update_all_lines(self, lines, points, scheme, bp_dict):
        for line, bps in zip(lines, scheme):
            self.update_line(line, points, bps, bp_dict)

    def update(self, framenum, framedict, all_points, scheme, bp_dict, cmap, ax, low, high):
        ax.clear()
        nparts = len(bp_dict)
        if framenum in framedict:
            points = all_points[:, framenum]
        else:
            points = np.ones((nparts, 3)) * np.nan

        ax.axes.set_xlim3d(left=low[0], right=high[0])
        ax.axes.set_ylim3d(bottom=low[1], top=high[1])
        ax.axes.set_zlim3d(bottom=low[2], top=high[2])
        self.connect_all(ax, points, scheme, bp_dict, cmap)
        return ax
