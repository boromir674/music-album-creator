# -*- coding: utf-8 -*-

import os
import re
import time


class StringToDictParser(object):
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
        if not all(
            0 <= len(x) <= len(self.entities) + len(self.separators)
            and all(type(y) == str for y in x)
            for x in design
        ):
            raise RuntimeError
        if not all(
            all(StringToDictParser.check.match(y) for y in x if y.startswith('s'))
            for x in design
        ):
            raise RuntimeError
        rregs = [RegexSequence([_ for _ in self._yield_reg_comp(d)]) for d in design]
        return max([r.search_n_dict(title) for r in rregs], key=lambda x: len(x))

    def _yield_reg_comp(self, kati):
        for k in kati:
            if k.startswith('s'):
                yield self.separators[int(StringToDictParser.check.match(k).group(1)) - 1]
            else:
                yield self.entities[k]


class AlbumInfoEntity(object):
    def __init__(self, name, reg):
        self.name = name
        self.reg = reg

    def __str__(self):
        return self.reg


class RegexSequence(object):
    def __init__(self, data):
        self._keys = [d.name for d in data if hasattr(d, 'name')]
        self._regex = r'{}'.format(''.join(str(d) for d in data))

    def search_n_dict(self, string):
        return dict(
            _
            for _ in zip(
                self._keys,
                list(
                    getattr(
                        re.search(self._regex, string),
                        'groups',
                        lambda: len(self._keys) * [''],
                    )()
                ),
            )
            if _[1]
        )


class StringParser(object):
    __instance = None
    # we take care of compiling the below regexes with the re.X flag
    # because they contain whitespaces on purpose for better readability
    # VERBOSE = X = sre_compile.SRE_FLAG_VERBOSE # ignore whitespace and comments

    # r"(?: {track_number} {sep1})? ( {track_name} ) {sep2} ({hhmmss})"
    regexes = {
        'track_number': r'\d{1,2}',  # we know this will try to match as many as possible with back-tracking ;-)
        'sep1': r"(?: [\t\ ]* [\.\-\,)]+ )? [\t ]*",
        'track_word_first_char': r"[\wα-ωΑ-Ω'\x86-\xce\u0384-\u03CE]",
        'track_word_char': r"[\.\w\-’':!\xc3\xa8α-ωΑ\-Ω\x86-\xce\u0384-\u03CE]",
        # 'track_word': r"\(?[\wα-ωΑ-Ω'\x86-\xce\u0384-\u03CE][\w\-’':!\xc3\xa8α-ωΑ\-Ω\x86-\xce\u0384-\u03CE]*\)?",
        'track_sep': r'[\t\ ,]+',
        'sep2': r'(?: [\t\ ]* [\-.]+ [\t\ ]* | [\t\ ]+ )',
        'extension': r'\.mp[34]',
        'hhmmss': r'(?:\d?\d:)*\d?\d',
    }

    ## to parse from youtube video title string
    sep1 = r'[\t ]*[\-\.][\t ]*'
    sep2 = r'[\t \-\.]+'
    year = r'\(?(\d{4})\)?'
    art = r'([\w ]*\w)'
    alb = r'([\w ]*\w)'

    album_info_parser = StringToDictParser(
        {'artist': art, 'album': alb, 'year': year}, [sep1, sep2]
    )

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(cls, StringParser).__new__(cls)
            cls.regexes[
                'track_word'
            ] = r'\(?{track_word_first_char}{track_word_char}*\)?'.format(**cls.regexes)
            cls.regexes['track_name'] = r'{track_word}(?:{track_sep}{track_word})*'.format(
                **cls.regexes
            )
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
        return cls.album_info_parser(
            video_title,
            design=[
                ['artist', 's1', 'album', 's2', 'year'],
                ['artist', 's1', 'album'],
                ['album', 's2', 'year'],
                ['album'],
            ],
        )

    # Uses the cls.regexes
    # PARSE filenames
    @classmethod
    def parse_track_number_n_name(cls, file_name):
        """Call this method to get a dict like {'track_number': 'number', 'track_name': 'name'} from input file name with format like '1. - Loyal to the Pack.mp3'; number must be included!"""
        return dict(
            zip(
                ['track_number', 'track_name'],
                list(
                    re.compile(
                        r"(?: ({track_number}) {sep1})? ( {track_name} ) {extension}$".format(
                            **cls.regexes
                        ),
                        re.X,  # VERBOSE = X = sre_compile.SRE_FLAG_VERBOSE # ignore whitespace and comments
                    )
                    .search(os.path.basename(file_name))
                    .groups()
                ),
            )
        )
        # return dict(zip(['track_number', 'track_name'], list(re.compile(r'({}){}({}){}$'.format(cls.track_number, cls.sep2, cls.track_name, cls.extension)).search(file_name).groups())))

    # Uses the cls.regexes
    @classmethod
    def _parse_track_line(cls, track_line):
        """
        Parses a string line such as '01. Doteru 3:45' into ['Doteru', '3:45']\n
        :param track_line:
        :return: the parsed items
        :rtype: list
        """
        # regex = re.compile(r"""^(?:\d{1,2}(?:[\ \t]*[\.\-,][\ \t]*|[\t\ ]+))?  # potential track number (eg 01) included is ignored
        #                             ([\w\'\(\) \-’]*[\w)])                       # track name
        #                             (?:[\t ]+|[\t ]*[\-\.]+[\t ]*)            # separator between name and time
        #                             ((?:\d?\d:)*\d?\d)$                       # time in hh:mm:ss format""", re.X)
        # regex = re.compile(r"^(?:{}{})?({}){}({})$".format(cls.track_number, cls.number_name_sep, cls.track_name, cls.sep, cls.hhmmss))
        regex = re.compile(
            r"(?: {track_number} {sep1})? ( {track_name} ) {sep2} ({hhmmss})".format(
                **cls.regexes
            ),
            re.X,
        )
        return list(regex.search(track_line.strip()).groups())

    # PARSE tracks info multiline
    @classmethod
    def parse_hhmmss_string(cls, tracks):
        """Call this method to transform a '\n' separabale string of album tracks (eg copy-pasted from video description) to a list of lists. Inner lists contains [track_name, hhmmss_formated time].\n
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
            except AttributeError as e:
                print(
                    "Couldn't parse line {}: '{}'. Please use a format as 'trackname - 3:45'".format(
                        i + 1, line
                    )
                )
                raise e

    # CONVERT durations to timestamps tuples (segmentation start-end pair)
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
            timestamps.append(cls.add(timestamps[i - 1], lines[i - 1][-1]))
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
        return cls.hhmmss_format(cls.to_seconds(timestamp1) + cls.to_seconds(duration))

    ###########################
    @staticmethod
    def to_seconds(timestamp):
        """Call this method to transform a hh:mm:ss formatted string timestamp to its equivalent duration in seconds as an integer"""
        return sum([60**i * int(x) for i, x in enumerate(reversed(timestamp.split(':')))])

    @staticmethod
    def hhmmss_format(seconds):
        """Call this method to transform an integer representing time duration in seconds to its equivalent hh:mm:ss formatted string representeation"""
        return time.strftime('%H:%M:%S', time.gmtime(seconds))
