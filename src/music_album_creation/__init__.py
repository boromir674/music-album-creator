__version__ = '1.0.8a'

from .tracks_parsing import StringParser
from .metadata import MetadataDealer
from .format_classification import FormatClassifier

from .downloading import YoutubeDownloader
from .album_segmentation import AudioSegmenter

__all__ = ['StringParser', 'MetadataDealer', 'FormatClassifier', 'YoutubeDownloader', 'AudioSegmenter']
