import os
import pickle

from sklearn.svm import LinearSVC

from . import dataset_handler
from .dataset import scan_for_albums


class FormatClassifier:
    default_music_dir = os.path.expanduser('~/Music')

    def __init__(self, music_library_dir=''):
        if music_library_dir:
            self.music_library_dir = music_library_dir
        else:
            self.music_library_dir = self.default_music_dir
        self._estimator = LinearSVC(penalty='l2',
                                    loss='squared_hinge',  # 'hinge'
                                    dual=False,
                                    tol=1e-4,
                                    fit_intercept=False,  # False: data expected to be already centered
                                    verbose=0,
                                    max_iter=1000)

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
