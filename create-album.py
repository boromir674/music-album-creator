#!/usr/bin/python3

import os
import sys
import shutil
from time import sleep

import click


from downloading import youtube, DownloadError
from album_segmentation import AudioSegmenter
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
    if debug:
        _debug(directory)
    else:
        print('\n###################\n## ALBUM CREATOR ##\n###################\n\n')
        print('Please input a url corresponding to a music album uploaded as a youtube video.\n'
              'The video must have timestamps indicating the start of each track within the music\n'
              'album, other wise the operations below will fail.\n')
        video_url = input('   video url: ')
        print()
        youtube.download(video_url, directory, spawn=False, verbose=True, debug=True)  # force waiting before continuing execution, by not spawning a separate process

        album_file = os.path.join(directory, os.listdir(directory)[0])

        audio_segmenter = AudioSegmenter(target_directory=directory)
        if input_tracks_file:
            audio_segmenter.segment_from_file_handler(album_file, input_tracks_file)
        else:
            lines = []
            print('\n\nPlease input data, line by line, specifying the track name (extension is\n'
                      'inferred from album file if found there) and the start timestamp, in the\n'
                      'format: "track_name hh:mm:ss". Press return with no data to exit.\n')
            while True:
                line = input('track data: ')
                if line:
                    lines.append(line.strip().split())
                else:
                    break
            audio_segmenter.segment_from_list(album_file, lines)
        _create_album_folder(album_file, directory)


def _create_album_folder(album_file, directory):
    tracks = [_ for _ in os.listdir(directory) if _ != os.path.basename(album_file)]
    print('\n\nThese are the tracks created:\n')
    print('\n'.join(sorted([' {}'.format(t) for t in tracks])), '\n')

    # TODO replace with click expression
    while 1:
        answer = input("Copy them to a destination directory? yes/no: ")
        if answer.lower() == 'yes' or answer.lower() == 'y':
            destination_directory = input('destination directory: ')
            try:
                os.makedirs(destination_directory)
                for track in tracks:
                    destination_file_path = os.path.join(destination_directory, track)
                    if os.path.isfile(destination_file_path):
                        print(" File '{}' already exists. Skipping".format(os.path.basename(track),
                                                                           destination_directory))
                    else:
                        shutil.copyfile(os.path.join(directory, track), destination_file_path)
                break
            except PermissionError:
                print("You don't have permision to create a directory in path '{}'".format(destination_directory))


def _debug(directory):
    ratm_testify_url = 'https://www.youtube.com/watch?v=Q3dvbM6Pias'
    try:
        youtube.download(ratm_testify_url, directory,
                     spawn=False, debug=True, verbose=True)  # force waiting before continuing execution, by not spawning a separate process
    except DownloadError as e:
        print(e)
        sys.exit(1)

    album_file = os.path.join(directory, os.listdir(directory)[0])

    audio_segmenter = AudioSegmenter(target_directory=directory)
    lines = [['First-ten','00:00'],
             ['Second-forty', '00:10'],
             ['Third', '00:50']]
    audio_segmenter.segment_from_list(album_file, lines)
    _create_album_folder(album_file, directory)



if __name__ == '__main__':
    main()
