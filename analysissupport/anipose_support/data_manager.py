from anipose_support.project_manager import ProjectManager
import sys, os
import numpy as np
import pandas as pd



class DataManager(ProjectManager):
    def __init__(self, ProjectManager=None) -> None:
        for key, val in vars(ProjectManager).items():
            setattr(self, key, val)

    def process_triangulate(self, config=None, out=None, score_threshold=0.5, over_write=True):
        if out is None:
            out = self.pose2d_fnames

        if config is None:
            config = self.config

        if os.path.exists(self.output_fname):
            print('\nThe videos were triangulate before ...')
            if not over_write:
                print('To re-do the process, please try again with overwriting permission!')
                self.status_triangulate = True
                print('Loading the processed data ...')
                self.load_data()
                print('Finished loading data!')
                return
            else:
                print('Re-triangulating ...')

        points = out['points']
        self.all_scores = out['scores']
        self.n_cams, self.n_frames, self.n_joints, _ = points.shape

        self.body_parts = out['bodyparts']

        # remove points that are below threshold
        points[self.all_scores < score_threshold] = np.nan

        points_flat = points.reshape(self.n_cams, -1, 2)
        scores_flat = self.all_scores.reshape(self.n_cams, -1)

        points_3d = self.cgroup.triangulate(points_flat, progress=True)
        errors = self.cgroup.reprojection_error(points_3d, points_flat, mean=True)
        good_points = ~np.isnan(points[:, :, :, 0])
        self.all_scores[~good_points] = 2

        self.num_cams = np.sum(good_points, axis=0).astype('float')

        self.all_points_3d = points_3d.reshape(self.n_frames, self.n_joints, 3)
        self.all_errors = errors.reshape(self.n_frames, self.n_joints)
        self.all_scores[~good_points] = 2
        self.scores_3d = np.min(self.all_scores, axis=0)

        self.scores_3d[self.num_cams < 2] = np.nan
        self.all_errors[self.num_cams < 2] = np.nan
        self.num_cams[self.num_cams < 2] = np.nan
        self.M = np.identity(3)
        self.center = np.zeros(3)

        self.optim_data(config=config)

        self.status_triangulate = True

        return self.all_points_3d, self.all_errors, self.body_parts

    def optim_data(self, config=None):
        if config is None:
            config = self.config

        if config['triangulation']['optim']:
            self.all_errors[np.isnan(self.all_errors)] = 0
        else:
            self.all_errors[np.isnan(self.all_errors)] = 10000
        good = (self.all_errors < 100)
        self.all_points_3d[~good] = np.nan

        self.all_points_flat = self.all_points_3d.reshape(-1, 3)
        check = ~np.isnan(self.all_points_flat[:, 0])

        if np.sum(check) < 10:
            print('too few points to plot, skipping...')
            return

        self.low_points, self.high_points = np.percentile(self.all_points_flat[check], [1, 99], axis=0)

    def export_data(self, output_fname=None, config=None):
        if self.status_triangulate == False:
            print('The project is not triangulated. Please run process_triangulate first!')
            return

        if output_fname is None:
            output_fname = os.path.join(self.project_path, self.videos_tail + '.csv')

        if config is None:
            config = self.config

        dout = pd.DataFrame()
        for bp_num, bp in enumerate(self.body_parts):
            for ax_num, axis in enumerate(['x', 'y', 'z']):
                dout[bp + '_' + axis] = self.all_points_3d[:, bp_num, ax_num]
            dout[bp + '_error'] = self.all_errors[:, bp_num]
            dout[bp + '_ncams'] = self.num_cams[:, bp_num]
            dout[bp + '_score'] = self.scores_3d[:, bp_num]

        for i in range(3):
            for j in range(3):
                dout['M_{}{}'.format(i, j)] = self.M[i, j]

        for i in range(3):
            dout['center_{}'.format(i)] = self.center[i]

        dout['fnum'] = np.arange(self.n_frames)

        dout.to_csv(output_fname, index=False)

    def load_data(self, config=None, output_fname=None):
        if output_fname is None:
            output_fname = self.output_fname

        if config is None:
            config = self.config

        try:
            scheme = config['labeling']['scheme']
        except KeyError:
            scheme = []

        data = pd.read_csv(output_fname)
        cols = [x for x in data.columns if '_error' in x]

        if len(scheme) == 0:
            self.body_parts = [c.replace('_error', '') for c in cols]
        else:
            self.body_parts = sorted(set([x for dx in scheme for x in dx]))

        bp_dict = dict(zip(self.body_parts, range(len(self.body_parts))))

        self.all_points_3d = np.transpose(np.array([np.array(data.loc[:, (bp + '_x', bp + '_y', bp + '_z')])
                                                    for bp in self.body_parts], dtype='float64'), [1, 0, 2])

        self.all_errors = np.transpose(np.array([np.array(data.loc[:, bp + '_error'])
                                                 for bp in self.body_parts], dtype='float64'), [1, 0])

        self.scores_3d = np.transpose(np.array([np.array(data.loc[:, bp + '_score'])
                                                for bp in self.body_parts], dtype='float64'), [1, 0])

        self.num_cams = np.transpose(np.array([np.array(data.loc[:, bp + '_ncams'])
                                               for bp in self.body_parts], dtype='float64'), [1, 0])
        self.M = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                self.M[i, j] = data.loc[0, 'M_{}{}'.format(i, j)]

        self.center = np.zeros(3)
        for i in range(3):
            self.center[i] = data.loc[0, 'center_{}'.format(i)]

        self.n_frames = np.max(data.loc[:, 'fnum']) + 1
        self.optim_data(config=config)
