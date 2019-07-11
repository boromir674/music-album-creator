import os

from .dataset import DatasetHandler

dataset_handler = DatasetHandler(datasets_root_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)), "data"))
from .tracks_format_classifier import FormatClassifier

__all__ = ['FormatClassifier', 'dataset_handler']
