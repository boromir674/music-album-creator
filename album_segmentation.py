import os
import sys
import subprocess
from time import sleep


class AudioSegmenter:

    args = ['ffmpeg', '-i', '-acodec', 'copy', '-ss']
    _debug_flag_hash = {True: {},
                        False: {'stdout': subprocess.PIPE}}

    def __init__(self, target_directory='/tmp'):
        self._track_index_generator = None
        self._dir = target_directory

    @property
    def target_directory(self):
        return self._dir
    @target_directory.setter
    def target_directory(self, directory_path):
        self._dir = directory_path

    def _segment(self, *args, sleep_seconds=0.9, debug=True, verbose=False):
        sleep(sleep_seconds)
        album_file = args[0]
        track_file = args[1]

        start = args[2]
        end = None
        if 3 < len(args):
            end = args[3]
        self._args = self.args[:2] + [album_file] + self.args[2:] + [start] + (lambda: ['-to', str(end)] if end else [])() + [track_file]
        if verbose:
            print("Segmenting with '{}'".format(' '.join(self._args)))
        exit_code = subprocess.run(self._args, stderr=subprocess.STDOUT, **self._debug_flag_hash[debug]).returncode
        # exit_code = subprocess.call(self._args)
        return exit_code

    def _track_file(self, album_file):
        return lambda y: os.path.join(self._dir, '{} - {}{}'.format(next(self._track_index_generator),
                                                                  y,
                                                                  (lambda x: '.' + x.split('.')[-1] if len(x.split('.')) > 1 else '')(album_file)))

    def segment_from_list(self, album_file, data, **kwargs):
        self._track_index_generator = iter((lambda x: str(x) if 9 < x else '0'+str(x))(_) for _ in range(1, 100))
        exit_code = 0
        data = self._parse_data(data, album_file)
        try:
            self._check_data(data)
        except AssertionError:
            raise TrackTimestampsSequenceError("Wrong track starting timestamps?\n{}".format('\n'.join([' '.join(d[:2]) for d in data])))
        i = 0
        while exit_code == 0 and i < len(data) - 1:
            sleep(0.6)
            exit_code = self._segment(album_file, *data[i], **kwargs)
            i += 1
        if exit_code != 0:
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))
        exit_code = self._segment(album_file, *data[-1], **kwargs)
        if exit_code != 0:
            raise FfmpegCommandError("Command '{}' failed".format(' '.join(self._args)))

    def segment_from_file(self, album_file, tracks_file, **kwargs):
        with open(tracks_file, 'r') as f:
            data = [_.strip().split() for _ in f.readlines()]
        self.segment_from_list(album_file, data, **kwargs)

    def segment_from_file_handler(self, album_file, tracks_file_handler, **kwargs):
        data = [_.strip().split() for _ in tracks_file_handler.readlines()]
        self.segment_from_list(album_file, data, **kwargs)

    @staticmethod
    def _convert(timestamp):
        """assumes hh:mm:ss format"""
        values = [int(_) for _ in timestamp.split(':')]
        values.reverse()
        _ =  str(sum([num * 60**i for i, num in enumerate(values)]))
        return _

    def _check_data(self, data):
        for i, d in enumerate(data[:-1]):
            assert int(d[1]) < int(d[2])
            assert int(d[2]) <= int(data[i+1][1])

    def _parse_data(self, data, album_file):
        for i, d in enumerate(data[:-1]):
            data[i][0] = self._track_file(album_file)(data[i][0])
            data[i][1] = self._convert(data[i][1])
            data[i].append(self._convert(data[i + 1][1]))
        data[-1][0] = self._track_file(album_file)(data[-1][0])
        data[-1][1] = self._convert(data[-1][1])
        return data

class FfmpegCommandError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class TrackTimestampsSequenceError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


audio_segmenter = AudioSegmenter()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print('Usage: python3 Album_segmentation.py AUDIO_FILE TRACKS_FILE')
        sys.exit(1)
    audio_segmenter.segment_from_file(sys.argv[1], sys.argv[2])