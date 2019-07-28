#!/usr/bin/env python3

import glob
import os
import shutil
import sys
import tempfile
from time import sleep

import click
import mutagen

from . import AudioSegmenter, FormatClassifier, MetadataDealer, StringParser
# 'front-end', interface, interactive dialogs are imported below
from .dialogs import DialogCommander as inout
from .downloading import (CMDYoutubeDownloader, InvalidUrlError,
                          TokenParameterNotInVideoInfoError,
                          UnavailableVideoError)
from .tracks_parsing import TrackTimestampsSequenceError, WrongTimestampFormat

if os.name == 'nt':
    from pyreadline import Readline
    readline = Readline()

this_dir = os.path.dirname(os.path.realpath(__file__))


def music_lib_directory(verbose=True):
    music_dir = os.getenv('MUSIC_LIB_ROOT', None)
    if music_dir is None:
        print("Please set the environment variable MUSIC_LIB_ROOT to point to a directory that stores music.")
        sys.exit(0)
    if not os.path.isdir(music_dir):
        try:
            os.makedirs(music_dir)
            if verbose:
                print("Created directory '{}'".format(music_dir))
        except (PermissionError, FileNotFoundError) as e:
            print(e)
            sys.exit(1)
    return music_dir


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
@click.option('--video_url', '-u', help='the youtube video url')
def main(tracks_info, track_name, track_number, artist, album_artist, video_url):
    # CONFIG of the 'app' #
    directory = os.path.join(tempfile.gettempdir(), 'gav')
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.mkdir(directory)

    music_dir = music_lib_directory(verbose=True)
    print("Music library: {}".format(music_dir))

    ## Render Logo
    inout.logo()

    print('\n')
    if not video_url:
        video_url = inout.input_youtube_url_dialog()
        print('\n')

    ## Init
    youtube = CMDYoutubeDownloader()
    audio_segmenter = AudioSegmenter(target_directory=directory)

    ## DOWNLOAD
    done = False
    while not done:
        try:
            youtube.download(video_url, directory, spawn=False, verbose=True, supress_stdout=False)  # force waiting before continuing execution, by not spawning a separate process
            done = True
        except TokenParameterNotInVideoInfoError as e:
            print(e, '\n')
            if inout.update_and_retry_dialog()['update-youtube-dl']:
                youtube.update_backend()
            else:
                print("Exiting ..")
                sys.exit(1)
        except (InvalidUrlError, UnavailableVideoError) as e:
            print(e, '\n')
            video_url = inout.input_youtube_url_dialog()
            print('\n')
        except Exception as e:
            print(e, '\n')
            print("Exiting ..")
            sys.exit(1)
    print('\n')

    album_file = os.path.join(directory, os.listdir(directory)[0])
    print("Album file: {}".format(album_file))
    print(os.path.basename(album_file))
    if os.path.basename(album_file) == '_.mp3':
        from .web_parsing import video_title
        guessed_info = StringParser.parse_album_info(video_title(video_url)[0])
    else:
        guessed_info = StringParser.parse_album_info(album_file)

    ### RECEIVE TRACKS INFORMATION
    if tracks_info:
        with open(tracks_info, 'r') as f:
            tracks_string = f.read().strip()
    else:
        sleep(0.50)
        tracks_string = inout.interactive_track_info_input_dialog().strip()
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
    answer = inout.track_information_type_dialog(prediction={1: 'durations'}.get(int(predicted_label), 'timestamps'))

    if answer.startswith('Durations'):
        tracks_data = StringParser.duration_data_to_timestamp_data(tracks_data)
    try:  # SEGMENTATION
        audio_file_paths = audio_segmenter.segment_from_list(album_file, tracks_data, supress_stdout=False, supress_stderr=False, verbose=True, sleep_seconds=0.4)
    except TrackTimestampsSequenceError as e:
        print(e)
        sys.exit(1)
        # TODO capture ctrl-D to signal possible change of type from timestamp to durations and vice-versa...
        # in order to put the above statement outside of while loop

    durations = [StringParser.time_format(getattr(mutagen.File(os.path.join(directory, t)).info, 'length', 0)) for t in audio_file_paths]
    max_row_length = max(len(_[0]) + len(_[1]) for _ in zip(audio_file_paths, durations))
    print("\n\nThese are the tracks created.\n")
    print('\n'.join(sorted([' {}{}  {}'.format(t, (max_row_length - len(t) - len(d)) * ' ', d) for t, d in zip(audio_file_paths, durations)])), '\n')

    ### STORE TRACKS IN DIR in MUSIC LIBRARY ROOT
    while 1:
        album_dir = inout.album_directory_path_dialog(music_dir, **guessed_info)
        try:
            os.makedirs(album_dir)
        except FileExistsError:
            if not inout.confirm_copy_tracks_dialog(album_dir):
                continue
        except FileNotFoundError:
            print("The selected destination directory '{}' is not valid.".format(album_dir))
            continue
        except PermissionError:
            print("You don't have permision to create a directory in path '{}'".format(album_dir))
            continue
        try:
            for track in audio_file_paths:
                destination_file_path = os.path.join(album_dir, os.path.basename(track))
                if os.path.isfile(destination_file_path):
                    print(" File '{}' already exists. in '{}'. Skipping".format(os.path.basename(track), album_dir))
                else:
                    shutil.copyfile(track, destination_file_path)
            print("Album tracks reside in '{}'".format(album_dir))
            break
        except PermissionError:
            print("Can't copy tracks to '{}' folder. You don't have write permissions in this directory".format(album_dir))

    ### WRITE METADATA
    md = MetadataDealer()
    answers = inout.interactive_metadata_dialogs(**guessed_info)
    md.set_album_metadata(album_dir, track_number=track_number, track_name=track_name, artist=answers['artist'],
                          album_artist=answers['album-artist'], album=answers['album'], year=answers['year'], verbose=True)


class TabCompleter:
    """A tab completer that can either complete from the filesystem or from a list."""
    def pathCompleter(self, text, state):
        """This is the tab completer for systems paths. Only tested on *nix systems"""
        _ = readline.get_line_buffer().split()
        return [x for x in glob.glob(text + '*')][state]

    def createListCompleter(self, ll):
        """
        This is a closure that creates a method that autocompletes from the given list. Since the autocomplete
        function can't be given a list to complete from a closure is used to create the listCompleter function with a
        list to complete from.
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
