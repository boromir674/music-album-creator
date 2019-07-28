import os
import sys

import attr
from sklearn.svm import LinearSVC

from .dataset import DatasetHandler, scan_for_albums

if 2 < sys.version_info[0]:
    import pickle
else:
    import cPickle as pickle


dataset_handler = DatasetHandler(datasets_root_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)), "data"))
this_dir = os.path.dirname(os.path.realpath(__file__))


@attr.s
class FormatClassifier(object):
    default_music_dir = os.path.expanduser('~/Music')
    music_library_dir = attr.ib(init=True, default=attr.Factory(lambda self: self.default_music_dir, takes_self=True))
    _estimator = attr.ib(init=False, default=LinearSVC(penalty='l2',
                                                       loss='squared_hinge',  # 'hinge'
                                                       dual=False,
                                                       tol=1e-4,
                                                       fit_intercept=False,  # False: data expected to be already centered
                                                       verbose=0,
                                                       max_iter=1000))

    def fit(self, X, y, sample_weight=None):
        self._estimator.fit(X, y, sample_weight=sample_weight)

    @classmethod
    def infer_new(cls, train_set='new-random', nb_datapoints=100, music_library_dir=''):
        """
        :param str train_set: {'new-random', 'load'}
        :param int nb_datapoints:
        :return:
        """
        fc = FormatClassifier(music_library_dir=music_library_dir)
        if train_set == 'new-random':
            fc.fit(*dataset_handler.create_datapoints(scan_for_albums((lambda x: x if x else cls.default_music_dir)(music_library_dir)), nb_datapoints=nb_datapoints))
        elif train_set == 'load':
            fc.fit(*list(dataset_handler.load_dataset_split('train')))
        return fc

    @classmethod
    def load_version(cls):
        return cls.load(os.path.join(this_dir, 'data/{}'.format({
            2: 'py27_model.pickle',
            3: 'model.pickle'
        }[sys.version_info[0]])))

    def save(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, file_path):
        with open(file_path, 'rb') as f:
            r = pickle.load(f)
        return r

    def is_durations(self, lines):
        return self.predict([dataset_handler.feature_vector(lines)])[0]

    # def save(self):
    def predict(self, X):
        return self._estimator.predict(X)

    def score(self, X, y, sample_weight=None):
        return self._estimator.score(X, y, sample_weight=sample_weight)
