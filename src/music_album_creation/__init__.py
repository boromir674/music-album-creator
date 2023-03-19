__version__ = '1.3.2'

from os import path

from . import _logging
from .audio_segmentation import AudioSegmenter
from .metadata import MetadataDealer
from .tracks_parsing import StringParser

__all__ = ['StringParser', 'MetadataDealer', 'AudioSegmenter']
