__version__ = '1.3.2'

import logging.config
from os import path

from .audio_segmentation import AudioSegmenter
from .metadata import MetadataDealer
from .tracks_parsing import StringParser

logging.config.fileConfig(path.join(path.dirname(path.realpath(__file__)), 'logging.ini'), disable_existing_loggers=False)

logger = logging.getLogger(__name__)


__all__ = ['StringParser', 'MetadataDealer', 'AudioSegmenter']
