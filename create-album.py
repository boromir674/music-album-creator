#!/usr/bin/python3

import os
import sys
import glob
import shutil
import readline
from time import sleep

import click


from downloading import youtube, DownloadError
from album_segmentation import AudioSegmenter, TrackTimestampsSequenceError, FfmpegCommandError
# from .tracks_parsing import parser



# @click.command()
# @click.option('--name', prompt='Your name please')
# def hello(name):
#     click.echo('Hello %s!' % name)


# @click.command()
# @click.option('--_debug', prompt='Your name please')
# def hello(name):
#     click.echo('Hello %s!' % name)


@click.command()
@click.option(
    '--input_tracks_file',
    type=click.File('r'),
    help='File in which there is tracks information necessary to _segment a music ablum into tracks.'
         'If not provided, a prompt will allow you to type the input tracks information.',
)
@click.option('--debug', '-d', is_flag=True)
def main(input_tracks_file, debug):
    directory = '/tmp/gav'
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.mkdir(directory)


    # t.createListCompleter(["ab", "aa", "bcd", "bdf"])

    # readline.set_completer_delims('\t')
    # readline.parse_and_bind("tab: complete")

    # readline.set_completer(t.listCompleter)
    # ans = input("Complete from list ")

    if debug:
        album_file = _debug(directory)
    else:
        print('\n###################\n## ALBUM CREATOR ##\n###################\n\n')
        print('Please input a url corresponding to a music album uploaded as a youtube video.\n'
              'The video must have timestamps indicating the start of each track within the music\n'
              'album, other wise the operations below will fail.\n')
        video_url = input('   video url: ')
        print()
        youtube.download(video_url, directory, spawn=False, verbose=False, debug=True)  # force waiting before continuing execution, by not spawning a separate process
        print()
        album_file = os.path.join(directory, os.listdir(directory)[0])

        audio_segmenter = AudioSegmenter(target_directory=directory)
        if input_tracks_file:
            audio_segmenter.segment_from_file_handler(album_file, input_tracks_file, verbose=True, debug=False, sleep_seconds=0)
        else:
            sleep(0.70)
            while 1:
                lines = _input_data_dialog()
                try:
                    audio_segmenter.segment_from_list(album_file, lines, verbose=True, debug=False, sleep_seconds=0)
                    break
                except TrackTimestampsSequenceError as e:
                    print(e)
    _create_album_folder(album_file, directory)


def _create_album_folder(album_file, directory):
    tracks = [_ for _ in os.listdir(directory) if _ != os.path.basename(album_file)]
    print('\n\nThese are the tracks created:\n')
    print('\n'.join(sorted([' {}'.format(t) for t in tracks])), '\n')

    while 1:
        answer = input("Copy them to a destination directory? yes/no: ")
        if answer.lower() == 'yes' or answer.lower() == 'y':
            destination_directory = input('destination directory: ')
            # destination_directory = input('destination directory: ')
            try:
                os.makedirs(destination_directory)
                for track in tracks:
                    destination_file_path = os.path.join(destination_directory, track)
                    if os.path.isfile(destination_file_path):
                        print(" File '{}' already exists. Skipping".format(os.path.basename(track), destination_directory))
                    else:
                        shutil.copyfile(os.path.join(directory, track), destination_file_path)
                break
            except PermissionError:
                print("You don't have permision to create a directory in path '{}'".format(destination_directory))
        else:
            break

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
                return [c + " " for c in ll][state]

            else:
                return [c + " " for c in ll if c.startswith(line)][state]
        self.listCompleter = listCompleter


def _input_data_dialog():
    lines = []
    print('Please input data, line by line, specifying the track name (extension is\n'
          'inferred from album file if found there) and the start timestamp, in the\n'
          'format: "track_name hh:mm:ss". Press return with no data to exit.\n')
    while True:
        line = input('track data: ')
        if line:
            lines.append(line.strip().split())
        else:
            break
    print()
    return lines

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
    lines = [['First-ten','00:00'],
             ['Second-forty', '00:10'],
             ['Third', '00:50']]
    audio_segmenter.segment_from_list(album_file, lines, sleep_seconds=1, debug=False, verbose=True)
    return album_file
    # _create_album_folder(album_file, directory)


if __name__ == '__main__':
    t = TabCompleter()
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(t.pathCompleter)
    main()