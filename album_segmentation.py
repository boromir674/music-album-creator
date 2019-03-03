#!/usr/bin/python3

import re
import os
import sys
import time
import subprocess
from warnings import warn

from tracks_parsing import SParser


class AudioSegmenter:
    sep = '(?:[\t ]+|[\t ]*[\-\.]+[\t ]*)'
    timestamp_objects = {}
    args = ['ffmpeg', '-i', '-acodec', 'copy', '-ss']
    capture_stdout = {False: {},  # stdout stream is printed on terminal
                      True: {'stdout': subprocess.PIPE}}  # stdout stream is captured ie str(ro.stdout, encoding='utf-8'))

    def __init__(self, target_directory='/tmp'):
        self._track_index_generator = None
        self._dir = target_directory
        self._i = 0
        
    @property
    def target_directory(self):
        return self._dir
    @target_directory.setter
    def target_directory(self, directory_path):
        self._dir = directory_path

    @classmethod
    def _parse_string(cls, tracks):
        regex = re.compile('(?:\d{1,2}[ \t]*[\.\-,][ \t]*|[\t ]+)?([\w ]*\w)' + cls.sep + '((?:\d?\d:)*\d?\d)$')
        for i, line in enumerate(_.strip() for _ in tracks.split('\n')):
            if line == '':
                continue
            if regex.search(line):
                yield list(regex.search(line).groups())
            else:
                raise WrongTimestampFormat("Couldn't parse line {}: '{}'. Please use a format as 'trackname - 3:45'".format(i+1, line))

    @classmethod
    def parse_hhmmss_string(cls, tracks):
        return [_ for _ in cls._parse_string(tracks)]

    @classmethod
    def duration_data_to_timestamp_data(cls, duration_data):
        return [list(_) for _ in cls._gen_timestamp_data(duration_data)]

    @staticmethod
    def _gen_timestamp_data(duration_data):
        """
        :param list of lists duration_data: each inner list has as 1st element a track name and as 2nd the track duration in hh:mm:s format
        :return: list of lists with timestamps instead of durations ready to feed for segmentation
        :rtype: list
        """
        i = 1
        p = Timestamp('0:00')
        yield duration_data[0][0], str(p)
        while i < len(duration_data):
            yield duration_data[i][0], str(p + Timestamp(duration_data[i-1][1]))
            p += Timestamp(duration_data[i-1][1])
            i += 1

    def segment_from_file(self, album_file, tracks_file, supress_stdout=True, verbose=False, sleep_seconds=0.45):
        with open(tracks_file, 'r') as f:
            list_of_lists = [x for x in self._parse_string(f.read().strip())]
        self.segment_from_list(album_file, list_of_lists, supress_stdout=supress_stdout, verbose=verbose, sleep_seconds=sleep_seconds)

    def segment_from_list(self, album_file, data, supress_stdout=True, verbose=False, sleep_seconds=0):
        """

        :param str album_file:
        :param list data: list of lists. Each inner list must have 2 elements: track name and starting timestamp in hh:mm:ss
        :param bool supress_stdout:
        :param bool verbose:
        :param float sleep_seconds:
        :return:
        """
        if int(Timestamp(data[0][1])) != 0:
            raise TrackTimestampsSequenceError("First track ({}) is supposed to have a 0:00 timestamp. Instead {} found".format(data[0][0], data[0][1]))
        self._track_index_generator = iter((lambda x: str(x) if 9 < x else '0'+str(x))(_) for _ in range(1, 100))
        exit_code = 0
        try:
            data = self._parse_data(data, album_file)
        except (TrackTimestampsSequenceError, WrongTimestampFormat) as e:
            raise e
        audio_files = [x[0] for x in data]
        i = 0
        while exit_code == 0 and i < len(data) - 1:
            time.sleep(sleep_seconds)
            exit_code = self._segment(album_file, *data[i], supress_stdout=supress_stdout, verbose=verbose)
            i += 1
        if exit_code != 0:
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        exit_code = self._segment(album_file, *data[-1], supress_stdout=supress_stdout, verbose=verbose)
        if exit_code != 0:
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        return audio_files

    def _segment(self, *args, supress_stdout=True, verbose=False):
        album_file = args[0]
        track_file = args[1]

        start = args[2]
        end = None
        if 3 < len(args):
            end = args[3]
        self._args = self.args[:2] + [album_file] + self.args[2:] + [start] + (lambda: ['-to', str(end)] if end else [])() + [track_file]
        if verbose:
            print("Segmenting with '{}'".format(' '.join(self._args)))
        ro = subprocess.run(self._args, stderr=subprocess.STDOUT, **self.capture_stdout[supress_stdout])
        return ro.returncode

    def _parse_data(self, data, album_file):
        """
        :param list of lists data: each inner list should contain track title (no need for number and without extension)
        and starting time stamp in hh:mm:ss format
        :param str album_file:
        :return: each iner list contains track title and timestamp in seconds
        :rtype: list of lists
        """
        for self._i, d in enumerate(data[:-1]):
            if self.timestamp(data[self._i + 1][1]) <= self.timestamp(data[self._i][1]):
                raise TrackTimestampsSequenceError(
                    "Track '{} - {}' starting timestamp '{}' should be 'bigger' than track's '{} - {}'; '{}'".format(
                        self._i + 2, data[self._i + 1][0], data[self._i + 1][1],
                        self._i + 1, data[self._i][0], data[self._i][1]))
            data[self._i][0] = self._track_file(album_file)(data[self._i][0])
            data[self._i][1] = str(int(self.timestamp(data[self._i][1])))
            data[self._i].append(str(int(self.timestamp(data[self._i + 1][1]))))
        data[-1][0] = self._track_file(album_file)(data[-1][0])
        data[-1][1] = str(int(self.timestamp(data[-1][1])))
        return data

    @classmethod
    def timestamp(cls, hhmmss):
        if hhmmss in cls.timestamp_objects:
            return cls.timestamp_objects[hhmmss]
        try:
            cls.timestamp_objects[hhmmss] = Timestamp(hhmmss)
            return cls.timestamp_objects[hhmmss]
        except WrongTimestampFormat as e:
            raise e

    def _track_file(self, album_file):
        return lambda y: os.path.join(self._dir, '{} - {}{}'.format(next(self._track_index_generator),
                                                                  y,
                                                                  (lambda x: '.' + x.split('.')[-1] if len(x.split('.')) > 1 else '')(album_file)))


class Timestamp:
    def __init__(self, hhmmss):
        match = re.fullmatch('((\d?\d):){0,2}(\d?\d)', hhmmss)
        if not match:
            raise WrongTimestampFormat("Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss))
        values = [int(_) for _ in hhmmss.split(':')]
        if not all([0 <= _ <= 60 for _ in values]):
            raise WrongTimestampFormat("Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss))
        self._s = sum([60 ** i * int(x) for i, x in enumerate(reversed(values))])
        self._b = hhmmss

    @staticmethod
    def from_duration(seconds):
        return Timestamp(time.strftime('%H:%M:%S', time.gmtime(seconds)))
    def __repr__(self):
        return self._b
    def __str__(self):
        return self._b
    def __eq__(self, other):
        return str(self) == str(other)
    def __int__(self):
        return self._s
    def __lt__(self, other):
        return int(self) < int(other)
    def __le__(self, other):
        return int(self) <= int(other)
    def __gt__(self, other):
        return int(other) < int(self)
    def __ge__(self, other):
        return int(other) <= int(self)
    def __add__(self, other):
        return Timestamp.from_duration(int(self) + int(other))
    def __sub__(self, other):
        return Timestamp.from_duration(int(self) - int(other))


class FfmpegCommandError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
class TrackTimestampsSequenceError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
class WrongTimestampFormat(Exception):
    def __init__(self, msg):
        super().__init__(msg)


audio_segmenter = AudioSegmenter()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print('Usage: python3 Album_segmentation.py AUDIO_FILE TRACKS_FILE')
        sys.exit(1)
    try:
        audio_segmenter.segment_from_file(sys.argv[1], sys.argv[2], supress_stdout=True, verbose=True, sleep_seconds=0.45)
    except (TrackTimestampsSequenceError, WrongTimestampFormat) as e:
        print(e)
        sys.exit(1)