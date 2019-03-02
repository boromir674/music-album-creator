#!/usr/bin/python3

import re
import os
import sys
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
from tracks_parsing import SParser
from format_classification import FormatClassifier
from frontend.metadata_dialogs import track_information_type_dialog, interactive_track_info_input_dialog, \
    store_album_dialog, interactive_metadata_dialogs


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
        print('Please input a url corresponding to a music album uploaded as a youtube video.\n')
              # 'The video must have timestamps indicating the start of each track within the music\n'
              # 'album, other wise the operations below will fail.\n')
        if not url:
            video_url = input('   video url: ')
        else:
            video_url = url

        print('\n')
        youtube.download(video_url, directory, spawn=False, verbose=False, debug=False)  # force waiting before continuing execution, by not spawning a separate process

        print('\n')

        album_file = os.path.join(directory, os.listdir(directory)[0])
        # print('{}\n'.format(_format(getattr(mutagen.File(album_file).info, 'length', 0))))
        guessed_info = SParser.get_instance().parse_album_info(album_file)
        # print('Automatically parsed information:', guessed_info)
        audio_segmenter = AudioSegmenter(target_directory=directory)

        ### RECEIVE TRACKS INFORMATION
        fc = FormatClassifier.load("/data/projects/music-album-creator/format_classification/data/model.pickle")
        sleep(0.50)
        if tracks_info:  # if file given with tracks information (titles and timestamps in hh:mm:ss format)  # FROM FILE
            lines = SParser.parse_tracks_hhmmss(tracks_info.read())
        else:
            lines = interactive_track_info_input_dialog(SParser.parse_tracks_hhmmss)

        durations_flag = track_information_type_dialog(prediction=fc.is_durations([_[1] for _ in lines]))

        if durations_flag:
            lines = SParser.hhmmss_to_timestamps(lines)

        try:
            audio_files = audio_segmenter.segment_from_list(album_file, lines, verbose=True, debug=False, sleep_seconds=0)
        except TrackTimestampsSequenceError as e:
            print(e)

                # TODO capture ctrl-D to signal possible change of type from timestamp to durations and vice-versa...
                # in order to put the above statement outside of while loop

    durations = [SParser.get_instance().format(getattr(mutagen.File(os.path.join(directory, t)).info, 'length', 0)) for t in audio_files]
    max_row_length = max(len(_[0]) + len(_[1]) for _ in zip(audio_files, durations))
    print("\n\nThese are the tracks created from '{}' album\n".format(os.path.dirname(audio_files[0])))
    print('\n'.join(sorted([' {}{}  {}'.format(t, (max_row_length - len(t) - len(d)) * ' ', d) for t, d in zip(audio_files, durations)])), '\n')

    ### STORE TRACKS IN DIR in MUSIC LIBRARY ROOT
    album_dir = store_album_dialog(audio_files, music_lib=music_dir, **guessed_info)

    ### WRITE METADATA
    md = MetadataDealer()
    answers = interactive_metadata_dialogs(**guessed_info)
    md.set_album_metadata(album_dir, track_number=track_number, track_name=track_name, artist=answers['artist'],
                          album_artist=answers['album-artist'], album=answers['album'], year=answers['year'], verbose=True)


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


if __name__ == '__main__':
    completer = TabCompleter()
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.pathCompleter)
    main()