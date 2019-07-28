# -*- coding: utf-8 -*-

import os
import re
import time


class StringToDictParser:
    """Parses album information out of video title string"""
    check = re.compile(r'^s([1-9]\d*)$')

    def __init__(self, entities, separators):
        if not all(type(x) == str for x in separators):
            raise RuntimeError
        self.entities = {k: AlbumInfoEntity(k, v) for k, v in entities.items()}
        self.separators = separators

    def __call__(self, *args, **kwargs):
        title = args[0]
        design = kwargs['design']
        if not all(0 <= len(x) <= len(self.entities) + len(self.separators) and all(type(y) == str for y in x) for x in design):
            raise RuntimeError
        if not all(all(StringToDictParser.check.match(y) for y in x if y.startswith('s')) for x in design):
            raise RuntimeError
        rregs = [RegexSequence([_ for _ in self._yield_reg_comp(d)]) for d in design]
        return max([r.search_n_dict(title) for r in rregs], key=lambda x: len(x))

    def _yield_reg_comp(self, kati):
        for k in kati:
            if k.startswith('s'):
                yield self.separators[int(StringToDictParser.check.match(k).group(1)) - 1]
            else:
                yield self.entities[k]

class AlbumInfoEntity:
    def __init__(self, name, reg):
        self.name = name
        self.reg = reg

    def __str__(self):
        return self.reg


class RegexSequence:
    def __init__(self, data):
        self._keys = [d.name for d in data if hasattr(d, 'name')]
        self._regex = r'{}'.format(''.join(str(d) for d in data))

    def search_n_dict(self, string):
        return dict(_ for _ in zip(self._keys, list(getattr(re.search(self._regex, string), 'groups', lambda: len(self._keys)*[''])())) if _[1])


class StringParser:
    __instance = None

    regexes = {'track_number': r'\d{1,2}',
               'sep1': r"(?: [\t\ ]* [\.\-\)]+ )? [\t ]*",
               'track_word': r"\(?[\w'][\w\-’':]*\)?",
               'track_sep': r'[\t\ ,]+',
               'sep2': r'(?: [\t\ ]* [\-.]+ [\t\ ]* | [\t\ ]+ )',
               'extension': r'\.mp3',
               'hhmmss': r'(?:\d?\d:)*\d?\d'}

    ## to parse from youtube video title string
    sep1 = r'[\t ]*[\-\.][\t ]*'
    sep2 = r'[\t \-\.]+'
    year = r'\(?(\d{4})\)?'
    art = r'([\w ]*\w)'
    alb = r'([\w ]*\w)'

    album_info_parser = StringToDictParser({'artist': art, 'album': alb, 'year': year}, [sep1, sep2])

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
            cls.regexes['track_name'] = r'{track_word}(?:{track_sep}{track_word})*'.format(**cls.regexes)
        return cls.__instance

    ## STRING TO DICT
    @classmethod
    def parse_album_info(cls, video_title):
        """Call to parse a video title string into a hash (dictionary) of potentially all 'artist', 'album' and 'year' fields.\n
        Can parse patters:
         - Artist Album Year\n
         - Artist Album\n
         - Album Year\n
         - Album\n
        :param str video_title:
        :return: the exracted values as a dictionary having maximally keys: {'artist', 'album', 'year'}
        :rtype: dict
        """
        return cls.album_info_parser(video_title, design=[['artist', 's1', 'album', 's2', 'year'],
                                                          ['artist', 's1', 'album'],
                                                          ['album', 's2', 'year'],
                                                          ['album']])

    @classmethod
    def parse_track_number_n_name(cls, file_name):
        """Call this method to get a dict like {'track_number': 'number', 'track_name': 'name'} from input file name with format like '1. - Loyal to the Pack.mp3'; number must be included!"""
        return dict(zip(['track_number', 'track_name'], list(
            re.compile(r"(?: ({track_number}) {sep1})? ( {track_name} ) {extension}$".format(**cls.regexes), re.X).search(
                os.path.basename(file_name)).groups())))
        # return dict(zip(['track_number', 'track_name'], list(re.compile(r'({}){}({}){}$'.format(cls.track_number, cls.sep2, cls.track_name, cls.extension)).search(file_name).groups())))

    @classmethod
    def duration_data_to_timestamp_data(cls, duration_data):
        """Call this method to transform a list of 2-legnth lists of track_name - duration_hhmmss pairs to the equivalent list of lists but with starting timestamps in hhmmss format inplace of the durations.\n
        :param list duration_data: eg: [['Know your enemy', '3:45'], ['Wake up', '4:53'], ['Testify', '4:32']]
        :return: eg: [['Know your enemy', '0:00'], ['Wake up', '3:45'], ['Testify', '8:38']]
        :rtype: list
        """
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
            try:
                yield duration_data[i][0], str(p + Timestamp(duration_data[i-1][1]))
            except WrongTimestampFormat as e:
                raise e
            p += Timestamp(duration_data[i-1][1])
            i += 1

    # STRING TO LIST
    @classmethod
    def parse_hhmmss_string(cls, tracks):
        """Call this method to transform a '\n' separabale string of album tracks (eg copy-pasted from video description) to a list of lists. Inner lists contains [track_name, hhmmss_timestamp].\n
        :param str tracks:
        :return:
        """
        return [_ for _ in cls._parse_string(tracks)]

    @classmethod
    def _parse_string(cls, tracks):
        """
        :param str tracks: a '\n' separable string of lines coresponding to the tracks information
        :return:
        """
        # regex = re.compile('(?:\d{1,2}[ \t]*[\.\-,][ \t]*|[\t ]+)?([\w\'\(\) ]*[\w)])' + cls.sep + '((?:\d?\d:)*\d?\d)$')
        for i, line in enumerate(_.strip() for _ in tracks.split('\n')):
            if line == '':
                continue
            try:
                yield cls._parse_track_line(line)
            except AttributeError:
                raise WrongTimestampFormat("Couldn't parse line {}: '{}'. Please use a format as 'trackname - 3:45'".format(i + 1, line))

    @classmethod
    def _parse_track_line(cls, track_line):
        """Parses a string line such as '01. Doteru 3:45'"""
        # regex = re.compile(r"""^(?:\d{1,2}(?:[\ \t]*[\.\-,][\ \t]*|[\t\ ]+))?  # potential track number (eg 01) included is ignored
        #                             ([\w\'\(\) \-’]*[\w)])                       # track name
        #                             (?:[\t ]+|[\t ]*[\-\.]+[\t ]*)            # separator between name and time
        #                             ((?:\d?\d:)*\d?\d)$                       # time in hh:mm:ss format""", re.X)
        # regex = re.compile(r"^(?:{}{})?({}){}({})$".format(cls.track_number, cls.number_name_sep, cls.track_name, cls.sep, cls.hhmmss))
        regex = re.compile(r"(?: {track_number} {sep1})? ( {track_name} ) {sep2} ({hhmmss})".format(**cls.regexes), re.X)
        return list(regex.search(track_line.strip()).groups())

    @classmethod
    def convert_to_timestamps(cls, tracks_row_strings):
        """Call this method to transform a '\n' separabale string of album tracks (eg copy-pasted from the youtube video description) that represents durations (in hhmmss format)
        to a list of strings with each track's starting timestamp in hhmmss format.\n
        :param str tracks_row_strings:
        :return: the list of each track's timestamp
        :rtype: list
        """
        lines = cls.parse_hhmmss_string(tracks_row_strings)  # list of lists
        i = 1
        timestamps = ['0:00']
        while i < len(lines):
            timestamps.append(cls.add(timestamps[i-1], lines[i-1][-1]))
            i += 1
        return timestamps

    @classmethod
    def add(cls, timestamp1, duration):
        """
        :param str timestamp1: hh:mm:ss
        :param str duration: hh:mm:ss
        :return: hh:mm:ss
        :rtype: str
        """
        return cls.time_format(cls.to_seconds(timestamp1) + cls.to_seconds(duration))

    @staticmethod
    def to_seconds(timestamp):
        """Call this method to transform a hh:mm:ss formatted string timestamp to its equivalent duration in seconds as an integer"""
        return sum([60**i * int(x) for i, x in enumerate(reversed(timestamp.split(':')))])

    @staticmethod
    def time_format(seconds):
        """Call this method to transform an integer representing time duration in seconds to its equivalent hh:mm:ss formatted string representeation"""
        return time.strftime('%H:%M:%S', time.gmtime(seconds))

    @classmethod
    def convert_tracks_data(cls, data, album_file, target_directory=''):
        """
        Converts input Nx2 list of lists to Nx3 list of lists. The exception being the last list that has 2 elements\n
        The input list's inner lists' elements are 'track_name' and 'starting_timestamp' in hhmmss format.\n
        :param list of lists data: each inner list should contain track title (no need for number and without extension)
        and starting time stamp in hh:mm:ss format
        :param str album_file: the path to the audio file of the entire album to potentially segment
        :param str target_directory: path to desired directory path to store the potentially created album
        :return: each iner list contains track path and timestamp in seconds
        :rtype: list of lists
        """
        return [list(_) for _ in cls._generate_data(data, album_file, target_directory)]

    @classmethod
    def _generate_data(cls, data, album_file, target_directory):
        """
        Given a data list, with each element representing an album's track (as an inner 2-element list with 1st element the 'track_name' and 2nd a timetamp in hh:mm:ss format (the track starts it's playback at that timestamp in relation with the total album playtime), the path to the alum file at hand and the desired output directory or potentially storing the track files,
        generates 3-length tuples with the track_file_path, starting timestamp and ending timestamp. Purpose is for the yielded tripplets to be digested for audio segmentation. The exception being the last tuple yielded that has 2 elements; it naturally misses the ending timestamp.\n
        :param list data:
        :param str album_file:
        :param str target_directory:
        :returns: 3-element tuples with track_file_path, starting_timestamp, ending_timestamp
        :rtype: tuple
        """
        cls.__album_file = album_file
        cls.__target_directory = target_directory
        cls.__track_index_generator = iter((lambda x: str(x) if 9 < x else '0' + str(x))(_) for _ in range(1, len(data) + 1))
        for i in range(len(data)-1):
            if Timestamp(data[i + 1][1]) <= Timestamp(data[i][1]):
                raise TrackTimestampsSequenceError(
                    "Track '{} - {}' starting timestamp '{}' should be 'bigger' than track's '{} - {}'; '{}'".format(
                        i + 2, data[i + 1][0], data[i + 1][1],
                        i + 1, data[i][0], data[i][1]))
            yield (
                cls.__track_file(data[i][0]),
                str(int(Timestamp(data[i][1]))),
                str(int(Timestamp(data[i + 1][1])))
            )
        yield (
            cls.__track_file(data[-1][0]),
            str(int(Timestamp(data[-1][1]))),
        )

    @classmethod
    def __track_file(cls, track_name):
        return os.path.join(cls.__target_directory, '{} - {}{}'.format(
            next(cls.__track_index_generator),
            track_name,
            (lambda x: '.' + x.split('.')[-1] if len(x.split('.')) > 1 else '')(cls.__album_file)))


class Timestamp:
    instances = {}

    @classmethod
    def __str(cls, element):
        if len(element) == 1:
            return '0{}'.format(int(element))
        return element

    @classmethod
    def __pos(cls, array):
        i = 0
        while i < len(array) and array[i] == 0:
            i += 1
        return i

    def __new__(cls, *args, **kwargs):
        hhmmss = args[0]
        m = re.compile(r'^(?:(\d?\d):){0,2}(\d?\d)$').search(hhmmss)
        if not m:
            raise WrongTimestampFormat("Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss))
        groups = hhmmss.split(':')
        if not all([0 <= int(_) <= 60 for _ in groups]):
            raise WrongTimestampFormat("Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss))

        ind = cls.__pos(groups)
        if len(groups) == 1:
            minlength_string = '{}:{}'.format(0, cls.__str(groups[0]))
        elif len(groups) - ind - 1 < 2:
            minlength_string = '{}:{}'.format(int(groups[-2]), cls.__str(groups[-1]))
        else:
            minlength_string = ':'.join([str(int(groups[ind]))] + [y for y in groups[ind + 1:]])
        stripped_string = ':'.join((str(int(_)) for _ in minlength_string.split(':')))

        if stripped_string in cls.instances:
            return cls.instances[stripped_string]
        x = super().__new__(cls)
        x.__minlength_string = minlength_string
        x.__stripped_string = stripped_string
        x._s = sum([60 ** i * int(x) for i, x in enumerate(reversed(groups))])
        cls.instances[x.__stripped_string] = x
        return x

    def __init__(self, hhmmss):
        pass

    @staticmethod
    def from_duration(seconds):
        return Timestamp(time.strftime('%H:%M:%S', time.gmtime(seconds)))

    def __int__(self):
        return self._s

    def __repr__(self):
        return self.__minlength_string

    def __str__(self):
        return self.__minlength_string

    def __hash__(self):
        return self._s

    def __eq__(self, other):
        return hash(self) == hash(other)

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


class WrongTimestampFormat(Exception): pass
class TrackTimestampsSequenceError(Exception): pass
