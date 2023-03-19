import re
import time

import attr

from music_album_creation.tracks_parsing import StringParser


#####################################
def segmentation_information(tracks_timestamps_info):
    """
    Converts input Nx2 (timestamps) list of lists to Nx3 (timestamps) list of lists. The exception being the last list that has 2 elements\n
    The input list's inner lists' elements are 'track_name' and 'starting_timestamp' in hhmmss format.\n
    :param list of lists tracks_timestamps_info: each inner list should contain track title (no need for number and without extension)
    and starting time stamp in hh:mm:ss format
    :return: each iner list contains track path and timestamp in seconds
    :rtype: list of lists
    """
    return [list(_) for _ in _generate_segmentation_spans(tracks_timestamps_info)]


def _generate_segmentation_spans(tracks_info):
    """
    Given a data list, with each element representing an album's track (as an inner 2-element list with 1st element the 'track_name' and 2nd a timetamp in hh:mm:ss format (the track starts it's playback at that timestamp in relation with the total album playtime), the path to the alum file at hand and the desired output directory or potentially storing the track files,
    generates 3-length tuples with the track_file_path, starting timestamp and ending timestamp. Purpose is for the yielded tripplets to be digested for audio segmentation. The exception being the last tuple yielded that has 2 elements; it naturally misses the ending timestamp.\n
    :param list tracks_info:
    :returns: 3-element tuples with track_file_path, starting_timestamp, ending_timestamp
    :rtype: tuple
    """
    track_index_generator = iter(
        (lambda x: str(x) if 9 < x else '0' + str(x))(_)
        for _ in range(1, len(tracks_info) + 1)
    )
    for i in range(len(tracks_info) - 1):
        if Timestamp(tracks_info[i + 1][1]) <= Timestamp(tracks_info[i][1]):
            raise TrackTimestampsSequenceError(
                "Track '{} - {}' starting timestamp '{}' should be 'bigger' than track's '{} - {}'; '{}'".format(
                    i + 2,
                    tracks_info[i + 1][0],
                    tracks_info[i + 1][1],
                    i + 1,
                    tracks_info[i][0],
                    tracks_info[i][1],
                )
            )
        yield (
            '{} - {}'.format(next(track_index_generator), tracks_info[i][0]),
            str(int(Timestamp(tracks_info[i][1]))),
            str(int(Timestamp(tracks_info[i + 1][1]))),
        )
    yield (
        '{} - {}'.format(next(track_index_generator), tracks_info[-1][0]),
        str(int(Timestamp(tracks_info[-1][1]))),
    )


def to_timestamps_info(tracks_durations_info):
    """Call this method to transform a list of 2-legnth lists of track_name - duration_hhmmss pairs to the equivalent list of lists but with starting timestamps in hhmmss format inplace of the durations.\n
    :param list tracks_durations_info: eg: [['Know your enemy', '3:45'], ['Wake up', '4:53'], ['Testify', '4:32']]
    :return: eg: [['Know your enemy', '0:00'], ['Wake up', '3:45'], ['Testify', '8:38']]
    :rtype: list
    """
    return [list(_) for _ in _gen_timestamp_data(tracks_durations_info)]


def _gen_timestamp_data(tracks_duration_info):
    """
    :param list of lists tracks_duration_info: each inner list has as 1st element a track name and as 2nd the track duration in hh:mm:s format
    :return: list of lists with timestamps instead of durations ready to feed for segmentation
    :rtype: list
    """
    i = 1
    p = Timestamp('0:00')
    yield tracks_duration_info[0][0], str(p)
    while i < len(tracks_duration_info):
        try:
            yield tracks_duration_info[i][0], str(
                p + Timestamp(tracks_duration_info[i - 1][1])
            )
        except WrongTimestampFormat as e:
            raise e
        p += Timestamp(tracks_duration_info[i - 1][1])
        i += 1


##############################################
@attr.s
class SegmentationInformation(object):
    """Encapsulates per track: ['track-name', 'start-timestamp', 'end-timestamp']. Last entry does not have 'end-timestamp' because the end of the album is implied."""

    tracks_info = attr.ib(init=True)

    @classmethod
    def from_tracks_information(cls, tracks_information, hhmmss_type):
        if hhmmss_type.lower().startswith('timestamp'):
            return SegmentationInformation(segmentation_information(list(tracks_information)))
        return SegmentationInformation(
            segmentation_information(to_timestamps_info(list(tracks_information)))
        )

    @classmethod
    def from_multiline(cls, string, hhmmss_type):
        return cls.from_tracks_information(
            TracksInformation.from_multiline(string), hhmmss_type
        )

    def __len__(self):
        return len(self.tracks_info)

    def __getitem__(self, item):
        return self.tracks_info[item]


@attr.s
class TracksInformation(object):
    """Encapsulates per track: ['track-name', 'hhmmss']"""

    tracks_data = attr.ib(init=True)
    track_names = attr.ib(
        init=False,
        default=attr.Factory(lambda self: [x[0] for x in self.tracks_data], takes_self=True),
    )
    hhmmss_list = attr.ib(
        init=False,
        default=attr.Factory(lambda self: [x[1] for x in self.tracks_data], takes_self=True),
    )

    @classmethod
    def from_multiline(cls, string):
        return TracksInformation(StringParser().parse_hhmmss_string(string))

    @classmethod
    def from_multiline_interactive(cls, interactive_dialog):
        return TracksInformation(StringParser().parse_hhmmss_string(interactive_dialog()))

    def __len__(self):
        return len(self.tracks_data)

    def __getitem__(self, item):
        return self.tracks_data[item]


##########################################################
class Timestamp(object):
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
            raise WrongTimestampFormat(
                "Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss)
            )
        groups = hhmmss.split(':')
        if not all([0 <= int(_) <= 60 for _ in groups]):
            raise WrongTimestampFormat(
                "Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss)
            )

        ind = cls.__pos(groups)
        if len(groups) == 1:
            minlength_string = '{}:{}'.format(0, cls.__str(groups[0]))
        elif len(groups) - ind - 1 < 2:
            minlength_string = '{}:{}'.format(int(groups[-2]), cls.__str(groups[-1]))
        else:
            minlength_string = ':'.join(
                [str(int(groups[ind]))] + [y for y in groups[ind + 1 :]]
            )
        stripped_string = ':'.join((str(int(_)) for _ in minlength_string.split(':')))

        if stripped_string in cls.instances:
            return cls.instances[stripped_string]
        x = super(Timestamp, cls).__new__(cls)
        x.__minlength_string = minlength_string
        x._a = 'gg'
        x.__stripped_string = stripped_string
        x.__s = sum([60**i * int(gr) for i, gr in enumerate(reversed(groups))])
        cls.instances[x.__stripped_string] = x
        return x

    def __init__(self, hhmmss):
        pass

    @staticmethod
    def from_duration(seconds):
        return Timestamp(time.strftime('%H:%M:%S', time.gmtime(seconds)))

    def __int__(self):
        return self.__s

    def __repr__(self):
        return self.__minlength_string

    def __str__(self):
        return self.__minlength_string

    def __hash__(self):
        return self.__s

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


class WrongTimestampFormat(Exception):
    pass


class TrackTimestampsSequenceError(Exception):
    pass
