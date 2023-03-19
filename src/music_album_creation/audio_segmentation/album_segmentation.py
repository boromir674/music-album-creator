import logging
import os
import subprocess
import tempfile
import time
from typing import Optional

from music_album_creation.ffmpeg import FFMPEG
from music_album_creation.tracks_parsing import StringParser

from .data import SegmentationInformation

logger = logging.getLogger(__name__)


ffmpeg = FFMPEG(
    os.environ.get('MUSIC_FFMPEG', 'ffmpeg')
)


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
        return [os.path.join(self._dir, '{}.mp4'.format(track_info[0]))] + track_info[1:]

    def segment(self, album_file, data, supress_stdout=True, supress_stderr=True, sleep_seconds=0):
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
        while exit_code == 0 and i < len(data) - 1:
            time.sleep(sleep_seconds)
            result = self._segment(album_file, *self._trans(list(data[i])), supress_stdout=supress_stdout, supress_stderr=supress_stderr)
            i += 1
        if result.exit_code != 0:
            logger.error("Fmmpeg exit code: %s", result.exit_code)
            logger.error("Ffmpeg st out: %s", result.stdout)
            logger.error("Fmmpeg stderr: %s", result.stderr)
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        result = self._segment(album_file, *self._trans(list(data[-1])), supress_stdout=supress_stdout, supress_stderr=supress_stderr)
        if result.exit_code != 0:
            logger.error("Fmmpeg exit code: %s", result.exit_code)
            logger.error("Ffmpeg st out: %s", result.stdout)
            logger.error("Fmmpeg stderr: %s", result.stderr)
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        return [os.path.join(self._dir, '{}.mp4'.format(list(x)[0])) for x in data]

    def segment_from_list(self, album_file, data, supress_stdout=True, supress_stderr=True, sleep_seconds=0):
        """
        Given an album audio file and data structure with tracks information, segments the audio file into audio tracks which get stored in the 'self.target_directory' folder.\n
        :param str album_file:
        :param list data: list of lists. Each inner list must have 2 elements: track name and starting timestamp in hh:mm:ss
        :param bool supress_stdout:
        :param bool supress_stderr:
        :param bool verbose:
        :param float sleep_seconds:
        :return: full paths to audio tracks
        """
        # if not re.search('0:00', data[0][1]):
        #     raise NotStartingFromZeroTimestampError("First track ({}) is supposed to have a 0:00 timestamp. Instead {} found".format(data[0][0], data[0][1]))

        exit_code = 0
        data = StringParser().convert_tracks_data(data, album_file, target_directory=self._dir)
        audio_file_paths = [x[0] for x in data]
        i = 0
        while exit_code == 0 and i < len(data) - 1:
            time.sleep(sleep_seconds)
            result = self._segment(album_file, *data[i], supress_stdout=supress_stdout, supress_stderr=supress_stderr)
            if result.exit_code != 0:
                logger.error("Fmmpeg exit code: %s", result.exit_code)
                logger.error("Ffmpeg st out: %s", result.stdout)
                logger.error("Fmmpeg stderr: %s", result.stderr)
                raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
            i += 1
        # if exit_code != 0:
        #     raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        result = self._segment(album_file, *data[-1], supress_stdout=supress_stdout, supress_stderr=supress_stderr)
        if result.exit_code != 0:
                logger.error("Fmmpeg exit code: %s", result.exit_code)
                logger.error("Ffmpeg st out: %s", result.stdout)
                logger.error("Fmmpeg stderr: %s", result.stderr)
                raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        # if exit_code != 0:
        #     raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        return audio_file_paths

    def segment_from_file(self, album_file, tracks_file, hhmmss_type, supress_stdout=True, supress_stderr=True, sleep_seconds=0):
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
            segmentation_info = SegmentationInformation.from_multiline(f.read().strip(), hhmmss_type)
        return self.segment(album_file, segmentation_info, supress_stdout=supress_stdout, supress_stderr=supress_stderr, sleep_seconds=sleep_seconds)

    def _segment(self, *args, **kwargs):
        album_file = args[0]
        track_file = args[1]
        # supress_stdout = kwargs['supress_stdout']
        # supress_stderr = kwargs['supress_stderr']

        start = args[2]  # starting timestamp
        end: Optional[str] = None  # end timestamp
        # if it is the last segment then end timestamp is the end of the album
        # and in that case the client code need to supply 3 arguments (not 4)
        if 3 < len(args):
            end = args[3]
        
        # args = ['ffmpeg', '-y', '-i', '-acodec', 'copy', '-ss']
        # self._args = args[:3] + ['{}'.format(album_file)] + args[3:] + [start] + (lambda: ['-to', str(end)] if end else [])() + ['{}'.format(track_file)]
        self._args = (
            '-y',
            '-i',
            str(album_file),  # youtube downloaded audio steam (ie local mp4 file)
            '-acodec',
            'copy',
            '-ss',
            start,
            *list((lambda: ['-to', str(end)] if end else [])()),
            str(track_file),
        )
        logger.info("Segmenting: ffmpeg '{}'".format(' '.join(self._args)))
        return ffmpeg(
            *self._args,
        )
        # return subprocess.check_call(self._args, **self.__std_parameters(supress_stdout, supress_stderr))
        # ro = subprocess.run(self._args, **self.__std_parameters(supress_stdout, supress_stderr))
        # return ro.returncode

    # @classmethod
    # def __std_parameters(cls, std_out_flag, std_error_flag):
    #     """If an input flag is True then the stream  (either 'out' or 'err') can be obtained ie obj = subprocess.run(..); str(obj.stdout, encoding='utf-8')).\n
    #     If an input flag is False then the stream will be normally outputted; ie at the terminal"""
    #     return {v: subprocess.PIPE for k, v in zip([std_out_flag, std_error_flag], ['stdout', 'stderr']) if k}


class FfmpegCommandError(Exception): pass


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print('Usage: python3 Album_segmentation.py AUDIO_FILE TRACKS_FILE')
        sys.exit(1)
    try:
        audio_segmenter = AudioSegmenter()
        audio_segmenter.segment_from_file(sys.argv[1], sys.argv[2], supress_stdout=True, supress_stderr=True, verbose=True, sleep_seconds=0.45)
    except Exception as e:
        print(e)
        sys.exit(1)
