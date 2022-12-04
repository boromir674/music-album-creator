import glob
import os
import re
from random import shuffle
from warnings import warn

import mutagen
from music_album_creation.tracks_parsing import StringParser
from tqdm import tqdm

sp = StringParser()


class DatasetHandler(object):
    __instance = None
    splits = ['train', 'dev', 'test']
    post_fix = '-split.txt'
    reg = r'^(\w+)-split\.txt$'  # reg to search in a directory expecting dataet files with names ending with '-split.txt'

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(cls, DatasetHandler).__new__(cls)
        dir_requested = kwargs['datasets_root_dir']
        if 'datasets_root_dir' in kwargs and bool(kwargs['datasets_root_dir']):
            c_globe = glob.glob('{}/*{}'.format(kwargs['datasets_root_dir'], cls.post_fix))
            try:
                cls.__instance._datasets = {re.match(cls.reg, os.path.basename(file)).group(1): file for file in c_globe}
            except AttributeError:
                raise RuntimeError("Unable to find datasets (txt files) in directory '{}'. Most probably one of [{}] did not match with regex '{}'.".format(dir_requested, ', '.join(str(_) for _ in c_globe), cls.reg))
            cls.__instance.datasets_root_dir = kwargs['datasets_root_dir']
        return cls.__instance

    @classmethod
    def get_instance(cls, datasets_root_dir=''):
        return DatasetHandler(datasets_root_dir=datasets_root_dir)

    def create_split(self, split, album_dirs, progress_bar=False):
        if progress_bar:
            gen = tqdm(new_gen(album_dirs), total=len(album_dirs) * 2, unit='datapoint')
        else:
            gen = new_gen(album_dirs)
        with open(os.path.join(self.datasets_root_dir, '{}{}'.format(split, self.post_fix)), 'w') as f:
            f.write('\n'.join('{} {}'.format(' '.join(str(el) for el in v), str(c)) for v, c in gen) + '\n')

    @staticmethod
    def feature_vector(hhmmss_list):
        return [StringParser.to_seconds(hhmmss_list[0])]

    def set_dataset_split(self, split, feature_vectors, labels):
        """
        Call this method to set a split {train, dev, test} with the input datapoints (feature vectors) and labels. Overwrites on disk if split found already.\n
        :param split:
        :param feature_vectors:
        :param labels:
        :return:
        """
        if split not in self.splits:
            raise RuntimeError("Requested to create '{}' split but only [{}] are supported.".format(split, ', '.join(self.splits)))
        if not os.path.isdir(self.datasets_root_dir):
            raise RuntimeError("No dedicated datasets directory found. Currently the 'datasets_root_dir' attribute is set to '{}'. Either manually "
                               "create the directory or use as DatasetHandler.get_instance(datasets_root_dir=your_valid_datasets_directory)".format(self.datasets_root_dir))
        self.save_dataset(os.path.join(self.datasets_root_dir, '{}{}'.format(split, self.post_fix)), feature_vectors, labels)

    @staticmethod
    def create_datapoints(album_dirs_list, nb_datapoints=None, progress_bar=False, class_ratio=0.5):
        """
        Creates datapoints with their corresponding features (currently single element vectors) and labels
        :param album_dirs_list:
        :param class_ratio:
        :return:
        """
        feature_vectors = []
        class_labels = []
        i = 0
        if nb_datapoints and type(nb_datapoints) != int:
            raise RuntimeError("Wrong type of 'nb_datapoints' parameter. It should either be an integer (to indicate number of datapoints to pick) or evaluate to False (to indicate taking all available datapoints). Instead '{}' was given".format(nb_datapoints))
        if progress_bar:
            if not nb_datapoints:
                gen = tqdm(new_gen(album_dirs_list), total=len(album_dirs_list) * 2, unit='datapoint')
            else:
                gen = tqdm(new_gen(album_dirs_list), total=nb_datapoints, unit='datapoint')
        else:
            gen = new_gen(album_dirs_list)
        for i, datapoint in enumerate(gen):
            feature_vectors.append(datapoint[0])  # feature vector
            class_labels.append(datapoint[1])  # class label
            if nb_datapoints is not None and i == nb_datapoints - 1:
                break
        if nb_datapoints and i < nb_datapoints - 1:
            warn("Requested {} datapoints but the {} albums available produced {}".format(nb_datapoints, len(album_dirs_list), len(feature_vectors)))
        return feature_vectors, class_labels

    def load_dataset_split(self, split):
        return self.load_dataset(os.path.join(self.datasets_root_dir, '{}{}'.format(split, self.post_fix)))

    @staticmethod
    def load_dataset(file_path):
        """
        :param file_path:
        :return: a list of feature vectors and a list of class labels. Assumes a single label per vector
        :rtype: tuple
        """
        with open(file_path, 'r') as f:
            rows = f.readlines()
        return [list(_) for _ in zip(*list([(_[:-1], _[-1]) for _ in [list(map(float, r.split(' '))) for r in rows]]))]

        # return zip(*map(lambda x: (x.split(' ')[:-1], x.split(' ')[-1]), rows))
        # return zip(*map(lambda x: (x[:-1], x[-1]), [map(int, r.split(' ')) for r in rows]))
        # [map(int, r.split(' ')) for r in rows]
        # return zip(*list([(_.split(' ')[:-1], _.split(' ')[-1]) for _ in rows]))

    @staticmethod
    def save_dataset(file_path, feature_vectors, class_labels):
        with open(file_path, 'w') as f:
            f.write('\n'.join('{} {}'.format(' '.join(str(el) for el in v), str(c)) for v, c in zip(feature_vectors, class_labels)) + '\n')


def scan_for_albums(music_library, random=False):
    """
    Returns album directories (as full paths) that heuristically were classified as music album folders
    :param music_library:
    :param bool random: whether to shuffle the albums randomlly
    :return: the album directory paths
    :rtype: list
    """
    import os
    albums = []
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(music_library):
        mp3s = glob.glob('{}/*.mp3'.format(root))
        if 2 < len(mp3s):  # heuristic: A minimum of 2 audio files is sufficient to constitute a music album
            albums.append(root)
    if random:
        shuffle(albums)
    return albums


# def create_from_custom_albums(file_path):
#     with open(file_path, 'r') as f:
#         lines = f.readlines()
#     return [_ for _ in new_gen(lines)]

def album_to_datapoints(album_dir):
    durs = [mutagen.File(f).info.length for f in glob.glob("{}/*.mp3".format(album_dir))]
    # durs = [get_duration(filename=f) for f in glob.glob("{}/*.mp3".format(album_dir))]

    # the sum of the durations and a is_album=1 flag (binary class) : an album
    d1 = [[durs[0]], 1]

    timestamps = sp.convert_to_timestamps('\n'.join('x {}'.format(sp.hhmmss_format(seconds)) for seconds in durs))

    # timestamps = sp.convert_to_timestamps('\n'.join('x {}'.format(_) for _ in hhmmss_durs))

    # the sum of the durations and a is_album=0 flag (binary class): not an album
    d2 = [[sp.to_seconds(timestamps[0])], 0]
    return [d1, d2]

def new_gen(album_dirs):
    for al in album_dirs:
        for dp in album_to_datapoints(al):
            yield dp
