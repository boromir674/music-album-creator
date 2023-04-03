#!/usr/bin/env python3

import glob
import logging
import os
import shutil
import sys
import time
from time import sleep

import click

from music_album_creation.ffprobe_client import FFProbeClient

from .audio_segmentation import (
    AudioSegmenter,
    SegmentationInformation,
    TracksInformation,
)
from .audio_segmentation.data import TrackTimestampsSequenceError

# 'front-end', interface, interactive dialogs are imported below
from .dialogs import DialogCommander as inout
from .downloading import (
    InvalidUrlError,
    TokenParameterNotInVideoInfoError,
    UnavailableVideoError,
)
from .ffmpeg import FFProbe
from .metadata import MetadataDealer
from .music_master import MusicMaster

ffprobe = FFProbe(os.environ.get('MUSIC_FFPROBE', 'ffprobe'))
ffprobe_client = FFProbeClient(ffprobe)


if os.name == 'nt':
    from pyreadline import Readline

    readline = Readline()

this_dir = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)


def music_lib_directory(verbose=True):
    music_dir = os.getenv('MUSIC_LIB_ROOT', None)
    if music_dir is None:
        print(
            "Please set the environment variable MUSIC_LIB_ROOT to point to a directory that stores music."
        )
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
    '--tracks_info',
    '-t_i',
    type=click.File('r'),
    help='File in which there is tracks information necessary to segment a music ablum into tracks.'
    'If not provided, a prompt will allow you to type the input tracks information.',
)
@click.option(
    '--track_name/--no-track_name',
    default=True,
    show_default=True,
    help='Whether to extract the track names from the mp3 files and write them as metadata correspondingly',
)
@click.option(
    '--track_number/--no-track_number',
    default=True,
    show_default=True,
    help='Whether to extract the track numbers from the mp3 files and write them as metadata correspondingly',
)
@click.option(
    '--artist',
    '-a',
    help="If given, then value shall be used as the PTE1 tag: 'Lead performer(s)/Soloist(s)'.  In the music player 'clementine' it corresponds to the 'artist' column (and not the 'Album artist column) ",
)
@click.option(
    '--album_artist',
    help="If given, then value shall be used as the TPE2 tag: 'Band/orchestra/accompaniment'.  In the music player 'clementine' it corresponds to the 'Album artist' column",
)
@click.option('--video_url', '-u', help='the youtube video url')
def main(tracks_info, track_name, track_number, artist, album_artist, video_url):
    music_dir = music_lib_directory(verbose=True)
    print("Music library: {}".format(music_dir))
    logger.error("Music library: {}".format(str(music_dir)))

    ## Render Logo
    inout.logo()

    print('\n')
    if not video_url:
        video_url = inout.input_youtube_url_dialog()
        print('\n')
    logger.error(f"URL {video_url}")
    ## Init
    music_master = MusicMaster(music_dir)
    # Segments Audio files into tracks and stores them in the system's temp dir (ie /tmp on Debian)
    audio_segmenter = AudioSegmenter()

    ## DOWNLOAD
    while 1:
        try:
            album_file = music_master.url2mp3(
                video_url, suppress_certificate_validation=False, force_download=False
            )
            break
        except TokenParameterNotInVideoInfoError as e:
            print(e, '\n')
            if inout.update_and_retry_dialog()['update-youtube-dl']:
                music_master.update_youtube()
            else:
                print("Exiting ..")
                sys.exit(1)
        except (InvalidUrlError, UnavailableVideoError) as e:
            print(e, '\n')
            video_url = inout.input_youtube_url_dialog()
            print('\n')
    print('\n')

    print("Album file: {}".format(album_file))

    ### RECEIVE TRACKS INFORMATION
    if tracks_info:
        tracks_info = TracksInformation.from_multiline(tracks_info.read().strip())
    else:  # Interactive track type input
        sleep(0.5)
        tracks_info = TracksInformation.from_multiline(
            inout.interactive_track_info_input_dialog().strip()
        )
        print()

    # Ask user if the input represents song timestamps (withing the whole playtime) OR
    # if the input represents song durations (that sum up to the total playtime)
    answer = inout.track_information_type_dialog()

    segmentation_info = SegmentationInformation.from_tracks_information(
        tracks_info, hhmmss_type=answer.lower()
    )

    # SEGMENTATION
    try:
        audio_file_paths = audio_segmenter.segment(
            album_file,
            segmentation_info,
            sleep_seconds=0,
        )
    except TrackTimestampsSequenceError as e:
        print(e)
        sys.exit(1)
        # TODO capture ctrl-D to signal possible change of type from timestamp to durations and vice-versa...
        # in order to put the above statement outside of while loop

    # TODO re-implement the below using the ffmpeg proxy
    durations = [
        time.strftime(
            '%H:%M:%S',
            time.gmtime(int(float(ffprobe_client.get_stream_info(f)['format']['duration']))),
        )
        for f in audio_file_paths
    ]

    # durations = [StringParser.hhmmss_format(getattr(mutagen.File(t).info, 'length', 0)) for t in audio_file_paths]
    max_row_length = max(len(_[0]) + len(_[1]) for _ in zip(audio_file_paths, durations))
    print("\n\nThese are the tracks created.\n")
    print(
        '\n'.join(
            sorted(
                [
                    ' {}{}  {}'.format(t, (max_row_length - len(t) - len(d)) * ' ', d)
                    for t, d in zip(audio_file_paths, durations)
                ]
            )
        ),
        '\n',
    )
    # TODO

    ### STORE TRACKS IN DIR in MUSIC LIBRARY ROOT
    while 1:
        print(type(music_dir), type(music_master.guessed_info))
        print(music_dir)
        print(music_master.guessed_info)
        album_dir = inout.album_directory_path_dialog(music_dir, **music_master.guessed_info)
        try:
            os.makedirs(album_dir)
        except FileExistsError:
            if not inout.confirm_copy_tracks_dialog(album_dir):
                continue
        except FileNotFoundError:
            print("The selected destination directory '{}' is not valid.".format(album_dir))
            continue
        except PermissionError:
            print(
                "You don't have permision to create a directory in path '{}'".format(album_dir)
            )
            continue
        try:
            for track in audio_file_paths:
                destination_file_path = os.path.join(album_dir, os.path.basename(track))
                if os.path.isfile(destination_file_path):
                    print(
                        " File '{}' already exists. in '{}'. Skipping".format(
                            os.path.basename(track), album_dir
                        )
                    )
                else:
                    shutil.copyfile(track, destination_file_path)
            print("Album tracks reside in '{}'".format(album_dir))
            break
        except PermissionError:
            print(
                "Can't copy tracks to '{}' folder. You don't have write permissions in this directory".format(
                    album_dir
                )
            )

    ### WRITE METADATA
    md = MetadataDealer()
    answers = inout.interactive_metadata_dialogs(**music_master.guessed_info)
    md.set_album_metadata(
        album_dir,
        track_number=track_number,
        track_name=track_name,
        artist=answers['artist'],
        album_artist=answers['album-artist'],
        album=answers['album'],
        year=answers['year'],
    )


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
