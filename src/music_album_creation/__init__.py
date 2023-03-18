__version__ = '1.3.2'

from . import _logging
from os import path

from .audio_segmentation import AudioSegmenter
from .metadata import MetadataDealer
from .tracks_parsing import StringParser


__all__ = ['StringParser', 'MetadataDealer', 'AudioSegmenter']
