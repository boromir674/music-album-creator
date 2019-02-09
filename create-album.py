#!/usr/bin/python3

import re
import os
import sys
import time
import glob
import shutil
import readline
import subprocess
from time import sleep
import mutagen
import click


from downloading import youtube, DownloadError
from album_segmentation import AudioSegmenter, TrackTimestampsSequenceError, FfmpegCommandError
from metadata import MetadataDealer
from frontend.metadata_dialogs import *


@click.command()
@click.option(
    '--tracks_info', '-t_i',
    type=click.File('r'),
    help='File in which there is tracks information necessary to segment a music ablum into tracks.'
         'If not provided, a prompt will allow you to type the input tracks information.',
)
@click.option('--track_name/--no-track_name', default=True, show_default=True, help='Whether to extract the track names from the mp3 files and write them as metadata correspondingly')
@click.option('--track_number/--no-track_number', default=True, show_default=True, help='Whether to extract the track numbers from the mp3 files and write them as metadata correspondingly')
@click.option('--artist', '-a', help="If given, then value shall be used as the PTE1 tag: 'Lead performer(s)/Soloist(s)'.  In the music player 'clementine' it corresponds to the 'artist' column (and not the 'Album artist column) ")
@click.option('--album_artist', help="If given, then value shall be used as the TPE2 tag: 'Band/orchestra/accompaniment'.  In the music player 'clementine' it corresponds to the 'Album artist' column")
@click.option('--debug', '-d', is_flag=True)
@click.option('--url', '-u', help='the youtube video url')
def main(tracks_info, track_name, track_number, artist, album_artist, debug, url):
    ## CONFIG of the 'app' ##
    directory = '/tmp/gav'
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.mkdir(directory)
    music_dir = '/media/kostas/freeagent/m'
    ###

    if debug:
        audio_files = _debug(directory)
        album_file = os.path.join(directory, os.listdir(directory)[0])
        guessed_info = _parse_artist_n_album(album_file)
    else:
        print('\n###################\n## ALBUM CREATOR ##\n###################\n\n')
        print('Please input a url corresponding to a music album uploaded as a youtube video.\n'
              'The video must have timestamps indicating the start of each track within the music\n'
              'album, other wise the operations below will fail.\n')
        if not url:
            video_url = input('   video url: ')
        else:
            video_url = url

        print('\n')
        youtube.download(video_url, directory, spawn=False, verbose=False, debug=True)  # force waiting before continuing execution, by not spawning a separate process

        print('\n')

        album_file = os.path.join(directory, os.listdir(directory)[0])
        print('{}\n'.format(_format(getattr(mutagen.File(album_file).info, 'length', 0))))
        guessed_info = _parse_artist_n_album(album_file)
        print('GEUSSES', guessed_info)
        audio_segmenter = AudioSegmenter(target_directory=directory)

        sleep(0.70)
        if tracks_info:  # if file given with tracks information (titles and timestamps in hh:mm:ss format)
            lines = _parse_track_information(tracks_info.read())
            audio_files = audio_segmenter.segment_from_list(album_file, lines, verbose=True, debug=False, sleep_seconds=0)
        else:
            while 1:
                lines = _input_data_dialog(multiline=True)
                try:
                    audio_files = audio_segmenter.segment_from_list(album_file, lines, verbose=True, debug=False, sleep_seconds=0)
                    break
                except TrackTimestampsSequenceError as e:
                    print(e)

    durations = [_format(getattr(mutagen.File(os.path.join(directory, t)).info, 'length', 0)) for t in audio_files]
    max_row_length = max(len(_[0]) + len(_[1]) for _ in zip(audio_files, durations))
    print("\n\nThese are the tracks created from '{}' album\n".format(os.path.dirname(audio_files[0])))
    print('\n'.join(sorted(
        [' {}{}  {}'.format(t, (max_row_length - len(t) - len(d)) * ' ', d) for t, d in zip(audio_files, durations)])), '\n')

    album_dir = store_album_dialog(audio_files, music_lib=music_dir, **guessed_info)

    md = MetadataDealer()
    answers = interactive(**guessed_info)
    md.set_album_metadata(album_dir, track_number=track_number, track_name=track_name, artist=answers['artist'],
                          album_artist=answers['album-artist'], album=answers['album'], year=answers['year'], verbose=True)


##### MULTILINE INPUT TRACK NAMES AND TIMESTAMPS (hh:mm:ss)
def _input_data_dialog(multiline=False):
    """Returns a list of lists. Each inner list """
    if multiline:
        print("Enter/Paste your tracks timestamps. Each line should represent a single track. Go cursor to lst empty line "
              "below your text and press Ctrl-D or Ctrl-Z (windows) to save it.")

        def input_lines(prompt=None):
            """Yields input lines from user until EOFError is raised."""
            while True:
                try:
                    yield input() if prompt is None else input(prompt)
                except EOFError:
                    break
                else:
                    prompt = None  # Only display prompt while reading first line.

        def multiline_input(prompt=None):
            """Reads a multi-line input from the user."""

            return os.linesep.join(input_lines(prompt=prompt))

        res = multiline_input()
        lines = _parse_track_information(res)
    else:
        track_number = 1
        lines = []
        print('Please input data, line by line, specifying the track name (extension is\n'
              'inferred from album file if found there) and the start timestamp, in the\n'
              'format: "track_name hh:mm:ss". Press return with no data to exit.\n')
        while True:
            line = input('track {} data: '.format(track_number))
            if line:
                lines.append(line.strip().split())
                track_number += 1
            else:
                break
        print()
    return lines

def _parse_track_information(tracks_row_strings):
    """Returns parsed track; title and timestamp in hh:mm:ss for each of the input's list elements. Skips potentially found track number as a natural order is assumed\n
        Returs a list of lists. Each inner list holds the captured groups in the parenthesis'"""
    regex = re.compile('(?:\d{1,2}[ \t]*[\.\-,][ \t]*|[\t ]+)?([\w ]*\w)(?:[\t ]*[\-\.][\t ]*|[\t ]+)((?:\d?\d:)*\d\d)')
    # regex = re.compile(r'(?:(?:\d{1,2})(?:[ \t]*[,\-\.][ \t]*|[ \t]+)|^)?(?:(?:\w+\b[ \t])*\w+)(?:[\t ]*[\-.][\t ]*|[\t ]+)((?:\d?\d:)*\d\d)')
    _ = [list(_) for _ in regex.findall(tracks_row_strings)]
    return _


class TabCompleter:
    """
    A tab completer that can either complete from
    the filesystem or from a list.
    """
    def pathCompleter(self, text, state):
        """
        This is the tab completer for systems paths.
        Only tested on *nix systems
        """
        line = readline.get_line_buffer().split()
        return [x for x in glob.glob(text + '*')][state]

    def createListCompleter(self, ll):
        """
        This is a closure that creates a method that autocompletes from the given list.
        Since the autocomplete function can't be given a list to complete from
        a closure is used to create the listCompleter function with a list to complete
        from.
        """
        def listCompleter(text, state):
            line = readline.get_line_buffer()

            if not line:
                print('CC1', c)
                return [c + " " for c in ll][state]

            else:
                print('CC2', c)
                return [c + " " for c in ll if c.startswith(line)][state]
        self.listCompleter = listCompleter


def _parse_artist_n_album(youtube_file):
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
    _reg = lambda x: re.compile(str('{}'*len(x)).format(*x))

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


def _debug(directory):
    ratm_testify_url = 'https://www.youtube.com/watch?v=Q3dvbM6Pias'
    try:
        youtube.download(ratm_testify_url, directory,
                     spawn=False, debug=False, verbose=True)  # force waiting before continuing execution, by not spawning a separate process
    except DownloadError as e:
        print(e)
        sys.exit(1)

    album_file = os.path.join(directory, os.listdir(directory)[0])

    audio_segmenter = AudioSegmenter(target_directory=directory)
    lines = [['First ten','0:00'],
             ['Second gav', '1:10'],
             ['Third', '01:50']]
    audio_files = audio_segmenter.segment_from_list(album_file, lines, sleep_seconds=1, debug=False, verbose=True)
    return audio_files
    # _store_album_dialog(album_file, directory)


def _format(duration):  # in seconds
    if not duration:
        return '0:00'
    res = time.strftime('%H:%M:%S', time.gmtime(duration))
    regex = re.compile('^0(?:0:?)*')
    substring = regex.match(res).group()
    return res.replace(substring, '')


if __name__ == '__main__':
    completer = TabCompleter()
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.pathCompleter)
    main()