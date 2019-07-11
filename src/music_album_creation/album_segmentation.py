#!/usr/bin/python3

import re
import time
import subprocess

from music_album_creation.tracks_parsing import StringParser


class AudioSegmenter:
    sep = r'(?:[\t ]+|[\t ]*[\-\.]+[\t ]*)'

    args = ['ffmpeg', '-i', '-acodec', 'copy', '-ss']

    def __init__(self, target_directory='/tmp'):
        self._dir = target_directory

    @property
    def target_directory(self):
        """The directory path that will serve as the destination for storing created tracks"""
        return self._dir

    @target_directory.setter
    def target_directory(self, directory_path):
        self._dir = directory_path

    def segment_from_file(self, album_file, tracks_file, supress_stdout=True, supress_stderr=True, verbose=False, sleep_seconds=0.45):
        """
        Given an album audio file and a file with track information, segments the audio file into audio tracks which get stored in the 'self.target_directory' folder.\n
        :param str album_file:
        :param str tracks_file:
        :param bool supress_stdout:
        :param bool supress_stderr:
        :param bool verbose:
        :param float sleep_seconds:
        :return:
        """
        with open(tracks_file, 'r') as f:
            list_of_lists = StringParser.parse_hhmmss_string(f.read().strip())
        self.segment_from_list(album_file, list_of_lists, supress_stdout=supress_stdout, supress_stderr=supress_stderr, verbose=verbose, sleep_seconds=sleep_seconds)

    def segment_from_list(self, album_file, data, supress_stdout=True, supress_stderr=True, verbose=False, sleep_seconds=0):
        """
        Given an album audio file and data structure with tracks information, segments the audio file into audio tracks which get stored in the 'self.target_directory' folder.\n
        :param str album_file:
        :param list data: list of lists. Each inner list must have 2 elements: track name and starting timestamp in hh:mm:ss
        :param bool supress_stdout:
        :param bool supress_stderr:
        :param bool verbose:
        :param float sleep_seconds:
        :return:
        """
        if not re.search('0:00', data[0][1]):
            raise NotStartingFromZeroTimestampError("First track ({}) is supposed to have a 0:00 timestamp. Instead {} found".format(data[0][0], data[0][1]))
        # self._track_index_generator = iter((lambda x: str(x) if 9 < x else '0'+str(x))(_) for _ in range(1, 100))
        exit_code = 0
        data = StringParser.convert_tracks_data(data, album_file, target_directory=self._dir)
        audio_files = [x[0] for x in data]
        i = 0
        while exit_code == 0 and i < len(data) - 1:
            time.sleep(sleep_seconds)
            exit_code = self._segment(album_file, *data[i], supress_stdout=supress_stdout, supress_stderr=supress_stderr, verbose=verbose)
            i += 1
        if exit_code != 0:
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        exit_code = self._segment(album_file, *data[-1], supress_stdout=supress_stdout, supress_stderr=supress_stderr, verbose=verbose)
        if exit_code != 0:
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        return audio_files

    def _segment(self, *args, supress_stdout=True, supress_stderr=True, verbose=False):
        album_file = args[0]
        track_file = args[1]

        start = args[2]
        end = None
        if 3 < len(args):
            end = args[3]
        self._args = self.args[:2] + [album_file] + self.args[2:] + [start] + (lambda: ['-to', str(end)] if end else [])() + [track_file]
        if verbose:
            print("Segmenting with '{}'".format(' '.join(self._args)))
        ro = subprocess.run(self._args, **self.__std_parameters(supress_stdout, supress_stderr))
        return ro.returncode

    @classmethod
    def __std_parameters(cls, std_out_flag, std_error_flag):
        """If an input flag is True then the stream  (either 'out' or 'err') can be obtained ie obj = subprocess.run(..); str(obj.stdout, encoding='utf-8')).\n
        If an input flag is False then the stream will be normally outputted; ie at the terminal"""
        return {v: subprocess.PIPE for k, v in zip([std_out_flag, std_error_flag], ['stdout', 'stderr']) if k}


class FfmpegCommandError(Exception): pass
class NotStartingFromZeroTimestampError(Exception): pass


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
