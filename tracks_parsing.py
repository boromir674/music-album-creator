# import urllib.request
#
# import urllib
# from bs4 import BeautifulSoup
# import re
#
#
# # url = "http://racing4everyone.eu/2015/10/25/formula-e-201516formula-e-201516-round01-china-race/"
#
#
# class TracksParser:
#
#     def parse_tracks(self, youtube_video_url):
#
#         page = urllib.request.urlopen(youtube_video_url)
#         o = page.read()
#         soup = BeautifulSoup(o, 'lxml')
#         '//*[@id="description"]/yt-formatted-string/a[1]'
#         '#description > yt-formatted-string > a:nth-child(1)'
#         '//*[@id="description"]/yt-formatted-string/a[2]'
#         mydivs = soup.findAll("div", {"class": "yt-simple-endpoint style-scope yt-formatted-string"})
#
#         # start = soup.find_all("start")
#
#         # with urllib.request.urlopen(youtube_video_url) as file_handler:
#
#         #     # fp = urllib.request.urlopen(youtube_video_url)
#         #     mystr = file_handler.read().decode('utf8')
#         # fp.close()
#
#         # print(mydivs)
#
#     def get_data(self):
#         return []
#
#
# parser = TracksParser()
#
#
# if __name__ == '__main__':
#     import sys
#
#     if len(sys.argv) < 2:
#         print('Usage: python3 tracks_parsing.py VIDEO_URL')
#         sys.exit(1)
#
#     url = sys.argv[1]
#     # url = 'https://www.youtube.com/watch?v=V5YOhcAof8I'
#     parser.parse_tracks(url)

import re
import time


class SParser:
    __instance = None
    sep = '(?:[\t ]+|[\t ]*[\-\.]+[\t ]*)'

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get_instance(cls):
        return SParser()

    @classmethod
    def _parse_line(cls):
        pass

    @classmethod
    def parse_tracks_user_input(cls, tracks_row_strings):
        """
        Returns parsed tracks: track_title and timestamp in hh:mm:ss format given the multiline string. Ignores potentially
        found track numbers in the start of each line  Returs a list of lists. Each inner list holds the captured groups in the parenthesis'\n
        :param str tracks_row_strings:
        :return: a list of lists with each inner list corresponding to each input string row and having 2 elements: the track name and the timestamp
        :rtype: list
        """
        regex   = re.compile('(?:\d{1,2}[ \t]*[\.\-,][ \t]*|[\t ]+)?([\w ]*\w)' + cls.sep + '((?:\d?\d:)*\d\d)')
        # regex = re.compile('(?:\d{1,2}(?:[ \t]*[\.\-,][ \t]*|[\t ])+)?([\w ]*\w)' + cls.sep + '((?:\d?\d:)*\d\d)')

        _ = [list(_) for _ in regex.findall(tracks_row_strings)]
        return _

    @classmethod
    def convert_to_timestamps(cls, tracks_row_strings):
        """Accepts tracks durations; one per row"""
        lines = cls.parse_tracks_user_input(tracks_row_strings)  # list of lists
        i = 1
        timestamps = ['0:00']
        while i < len(lines):
            timestamps[i] = cls.add(timestamps[i-1], lines[i-1][-1])
            i += 1
        return timestamps

    @classmethod
    def add(cls, timestamp1: str, duration: str) -> object:
        """
        :param str timestamp1: hh:mm:ss
        :param str duration: hh:mm:ss
        :return: hh:mm:ss
        :rtype: str
        """
        return cls.to_timestamp(cls.to_seconds(timestamp1) + cls.to_seconds(duration))

    @staticmethod
    def to_seconds(timestamp):
        return sum([60**i * int(x) for i, x in enumerate(timestamp.split(':'))])

    @staticmethod
    def to_timestamp(seconds):
        return time.strftime('%H:%M:%S', time.gmtime(seconds))

    @staticmethod
    def parse_album_info(youtube_file):
        """
        Can parse patters:
         - Artist Album Year\n
         - Album Year\n
         - Artist Album\n
         - Album\n
        :param youtube_file:
        :return: the exracted values as a dictionary having maximally keys: {'artist', 'album', 'year'}
        :rtype: dict
        """
        sep1 = '[\t ]*[\-\.][\t ]*'
        sep2 = '[\t \-\.]+'
        year = '\(?(\d{4})\)?'
        art = '([\w ]*\w)'
        alb = '([\w ]*\w)'
        _reg = lambda x: re.compile(str('{}' * len(x)).format(*x))

        reg1 = _reg([art, sep1, alb, sep2, year])
        m1 = reg1.search(youtube_file)
        if m1:
            return {'artist': m1.group(1), 'album': m1.group(2), 'year': m1.group(3)}

        m1 = _reg([alb, sep2, year]).search(youtube_file)
        if m1:
            return {'album': m1.group(1), 'year': m1.group(2)}

        reg2 = _reg([art, sep1, alb])
        m2 = reg2.search(youtube_file)
        if m2:
            return {'artist': m2.group(1), 'album': m2.group(2)}

        reg3 = _reg([alb])
        m3 = reg3.search(youtube_file)
        if m3:
            return {'album': m3.group(1)}
        return {}

    @staticmethod
    def format(duration):  # in seconds
        if not duration:
            return '0:00'
        res = time.strftime('%H:%M:%S', time.gmtime(duration))
        regex = re.compile('^0(?:0:?)*')
        substring = regex.match(res).group()
        return res.replace(substring, '')


# class TabCompleter:
#     """
#     A tab completer that can either complete from
#     the filesystem or from a list.
#     """
#     def pathCompleter(self, text, state):
#         """
#         This is the tab completer for systems paths.
#         Only tested on *nix systems
#         """
#         line = readline.get_line_buffer().split()
#         return [x for x in glob.glob(text + '*')][state]
#
#     def createListCompleter(self, ll):
#         """
#         This is a closure that creates a method that autocompletes from the given list.
#         Since the autocomplete function can't be given a list to complete from
#         a closure is used to create the listCompleter function with a list to complete
#         from.
#         """
#         def listCompleter(text, state):
#             line = readline.get_line_buffer()
#
#             if not line:
#                 return [c + " " for c in ll][state]
#
#             else:
#                 return [c + " " for c in ll if c.startswith(line)][state]
#         self.listCompleter = listCompleter
