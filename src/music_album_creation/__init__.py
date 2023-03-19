__version__ = '1.3.2'

from os import path

from . import _logging
from .audio_segmentation import AudioSegmenter
from .tracks_parsing import StringParser

__all__ = ['StringParser', 'AudioSegmenter']
