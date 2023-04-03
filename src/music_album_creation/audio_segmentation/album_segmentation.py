import logging
import os
import tempfile
import time
from typing import List, Optional

from music_album_creation.ffmpeg import FFMPEG

from .data import SegmentationInformation

logger = logging.getLogger(__name__)


ffmpeg = FFMPEG(os.environ.get('MUSIC_FFMPEG', 'ffmpeg'))

EXT = 'mp3'


class AudioSegmenter(object):
    def __init__(self, target_directory=tempfile.gettempdir()):
        self._dir = target_directory

    @property
    def target_directory(self):
        """The directory path that will serve as the destination for storing created tracks"""
        return self._dir

    @target_directory.setter
    def target_directory(self, directory_path):
        self._dir = directory_path

    def _trans(self, track_info):
        """Create (file) name of output track."""
        return [os.path.join(self._dir, f'{track_info[0]}.{EXT}')] + track_info[1:]

    def segment(self, album_file, data, sleep_seconds=0):
        """
        :param album_file:
        :param data:
        :param supress_stdout:
        :param supress_stderr:
        :param float sleep_seconds:
        :return:
        """
        exit_code = 0
        i = 0
        track_files: List[str] = []
        while exit_code == 0 and i < len(data) - 1:
            time.sleep(sleep_seconds)
            result = self._segment(
                album_file,
                *self._trans(list(data[i])),
            )
            if result.exit_code != 0:
                logger.error("Fmmpeg exit code: %s", result.exit_code)
                logger.error("Ffmpeg st out: %s", result.stdout)
                logger.error("Fmmpeg stderr: %s", result.stderr)
                raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
            track_files.append(list(data[i])[1])
            i += 1
        result = self._segment(
            album_file,
            *self._trans(list(data[-1])),
        )
        if result.exit_code != 0:
            logger.error("Fmmpeg exit code: %s", result.exit_code)
            logger.error("Ffmpeg st out: %s", result.stdout)
            logger.error("Fmmpeg stderr: %s", result.stderr)
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        # TODO: remove the need to hard-code extension. should know from download module
        # if we download youtube video as mp4 audio, then each track should probably be mp4 too
        # if we download youtube video as mp3 audio, then each track should probably be mp3 too
        return [os.path.join(self._dir, f'{list(x)[0]}.{EXT}') for x in data]

    def segment_from_file(
        self,
        album_file,
        tracks_file,
        hhmmss_type,
        supress_stdout=True,
        supress_stderr=True,
        sleep_seconds=0,
    ):
        """
        Assumes the hhmmss are starting timestamps. Given an album audio file and a file with track information, segments the audio file into audio tracks which get stored in the 'self.target_directory' folder.\n
        :param str album_file:
        :param str tracks_file:
        :param str hhmmss_type:
        :param bool supress_stdout:
        :param bool supress_stderr:
        :param float sleep_seconds:
        :return:
        """
        with open(tracks_file, 'r') as f:
            segmentation_info = SegmentationInformation.from_multiline(
                f.read().strip(), hhmmss_type
            )
        return self.segment(
            album_file,
            segmentation_info,
            supress_stdout=supress_stdout,
            supress_stderr=supress_stderr,
            sleep_seconds=sleep_seconds,
        )

    def _segment(self, *args, **kwargs):
        album_file = args[0]
        track_file = args[1]
        start = args[2]  # starting timestamp
        end: Optional[str] = None  # end timestamp

        # if it is the last segment then end timestamp is the end of the album
        # and in that case the client code need to supply 3 arguments (not 4)
        if 3 < len(args):
            end = args[3]

        # args = ['ffmpeg', '-y', '-i', '-acodec', 'copy', '-ss']
        # self._args = args[:3] + ['{}'.format(album_file)] + args[3:] + [start] + (lambda: ['-to', str(end)] if end else [])() + ['{}'.format(track_file)]
        # COPY web stream as it is (no custom encododing)
        # so cannot change the file extension to store
        # output extension is better kept to be guessed by ffmpeg from the input file
        self._args = (
            '-y',
            '-i',
            str(album_file),  # youtube downloaded audio steam (ie local mp4 file)
            # '-acodec',
            # 'copy',
            # 'AAC',
            # '-c:a',
            # 'libmp3lame',
            # '-qscale:a',
            # '9',  # max quality
            # '-ab',
            # '133k',
            '-ss',
            start,
            *list((lambda: ['-to', str(end)] if end else [])()),
            '-f',
            'mp3',
            str(track_file),
        )
        # self._args = (
        #     '-y',
        #     '-i',
        #     str(album_file),  # youtube downloaded audio steam (ie local mp4 file)
        #     '-acodec',
        #     'copy',
        #     '-ss',
        #     start,
        #     *list((lambda: ['-to', str(end)] if end else [])()),
        #     str(track_file).replace('mp4', 'mp3'),
        # )
        logger.info("Segmenting: ffmpeg '{}'".format(' '.join(self._args)))
        return ffmpeg(
            *self._args,
        )


class FfmpegCommandError(Exception):
    pass


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print('Usage: python3 Album_segmentation.py AUDIO_FILE TRACKS_FILE')
        sys.exit(1)
    try:
        audio_segmenter = AudioSegmenter()
        audio_segmenter.segment_from_file(
            sys.argv[1],
            sys.argv[2],
            supress_stdout=True,
            supress_stderr=True,
            verbose=True,
            sleep_seconds=0.45,
        )
    except Exception as e:
        print(e)
        sys.exit(1)
