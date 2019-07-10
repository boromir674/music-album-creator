#!/usr/bin/env python3

import os
import sys
import glob
import click
import shutil
import mutagen
import readline
import subprocess
from time import sleep

from . import StringParser, MetadataDealer, AudioSegmenter, FormatClassifier
from .tracks_parsing import TrackTimestampsSequenceError, WrongTimestampFormat

from .downloading import YoutubeDownloader, TokenParameterNotInVideoInfoError, InvalidUrlError, UnavailableVideoError

# 'front-end', interface, interactive dialogs are imported below
from .dialogs import track_information_type_dialog, interactive_track_info_input_dialog, \
    store_album_dialog, interactive_metadata_dialogs, input_youtube_url_dialog, update_and_retry_dialog


this_dir = os.path.dirname(os.path.realpath(__file__))


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
@click.option('--url', '-u', help='the youtube video url')
def main(tracks_info, track_name, track_number, artist, album_artist, url):
    # CONFIG of the 'app' #
    directory = '/tmp/gav'
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.mkdir(directory)
    music_dir = '/media/kostas/freeagent/m'

    ## Render Logo
    subprocess.call([os.path.join(this_dir, 'display-logo.sh')])

    print('\n')
    video_url = url
    if not url:
        video_url = input_youtube_url_dialog()
    print('\n')

    done = False
    while not done:
        try:
            YoutubeDownloader.download(video_url, directory, spawn=False, verbose=True, supress_stdout=False)  # force waiting before continuing execution, by not spawning a separate process
            done = True
        except TokenParameterNotInVideoInfoError as e:
            print(e, '\n')
            if update_and_retry_dialog()['update-youtube-dl']:
                print("About to execute '{}'".format(YoutubeDownloader.update_backend_command))
                _ = YoutubeDownloader.update_backend()
            else:
                print("Exiting ..")
                sys.exit(1)
        except (InvalidUrlError, UnavailableVideoError) as e:
            print(e, '\n')
            video_url = input_youtube_url_dialog()
            print('\n')
        except Exception as e:
            print(e, '\n')
            print("Exiting ..")
            sys.exit(1)
    print('\n')

    album_file = os.path.join(directory, os.listdir(directory)[0])
    guessed_info = StringParser.parse_album_info(album_file)
    audio_segmenter = AudioSegmenter(target_directory=directory)

    ### RECEIVE TRACKS INFORMATION
    if tracks_info:
        with open(tracks_info, 'r') as f:
            tracks_string = f.read().strip()
    else:
        sleep(0.50)
        tracks_string = interactive_track_info_input_dialog().strip()
        print()
    # Convert string with tracks and timestamps information to data structure
    try:
        tracks_data = StringParser.parse_hhmmss_string(tracks_string)
    except WrongTimestampFormat as e:
        print(e)
        sys.exit(1)

    ### PREDICTION SERVICE
    fc = FormatClassifier.load(os.path.join(this_dir, "format_classification/data/model.pickle"))
    predicted_label = fc.is_durations([_[1] for _ in tracks_data])
    # print('Predicted class {}; 0: timestamp input, 1:duration input'.format(predicted_label))
    answer = track_information_type_dialog(prediction={1: 'durations'}.get(int(predicted_label), 'timestamps'))

    if answer.startswith('Durations'):
        tracks_data = StringParser.duration_data_to_timestamp_data(tracks_data)
    try:  # SEGMENTATION
        audio_files = audio_segmenter.segment_from_list(album_file, tracks_data, supress_stdout=True, verbose=True, sleep_seconds=0.4)
    except TrackTimestampsSequenceError as e:
        print(e)
        sys.exit(1)
        # TODO capture ctrl-D to signal possible change of type from timestamp to durations and vice-versa...
        # in order to put the above statement outside of while loop

    durations = [StringParser.time_format(getattr(mutagen.File(os.path.join(directory, t)).info, 'length', 0)) for t in audio_files]
    max_row_length = max(len(_[0]) + len(_[1]) for _ in zip(audio_files, durations))
    print("\n\nThese are the tracks created.\n".format(os.path.dirname(audio_files[0])))
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
        _ = readline.get_line_buffer().split()
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
                return [c + " " for c in ll][state]
            else:
                return [c + " " for c in ll if c.startswith(line)][state]

        self.listCompleter = listCompleter


if __name__ == '__main__':
    completer = TabCompleter()
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.pathCompleter)
    main()
