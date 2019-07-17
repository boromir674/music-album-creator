import os
import shutil

from PyInquirer import prompt, Validator, ValidationError

# __all__ = ['store_album_dialog', 'interactive_metadata_dialogs']

#### INPUT URL
def input_youtube_url_dialog():
    """"""
    print('Please input a url corresponding to a music album uploaded as a youtube video.\n')
    video_url = input('   video url: ')
    return video_url


## HANDLE Token Error with update youtube-dl and retry download same url dialog
def update_and_retry_dialog():
    questions = [
        {
            'type': 'confirm',
            'name': 'update-youtube-dl',
            'message': "Update 'youtube-dl' backend?)",
            'default': True,
        }
    ]
    answer = prompt(questions)
    return answer


##### MULTILINE INPUT TRACK NAMES AND TIMESTAMPS (hh:mm:ss)
def track_information_type_dialog(prediction=''):
    """Returns a parser of track hh:mm:ss multiline string"""
    if prediction == 'timestamps':
        choices = ['Timestamps (predicted)', 'Durations']
    elif prediction == 'durations':
        choices = ['Durations (predicted)', 'Timestamps']
    else:
        choices = ['Timestamps', 'Durations']
    questions = [
        {
            'type': 'list',  # navigate with arrows through choices
            'name': 'how-to-input-tracks',
            # type of is the format you prefer to input for providing the necessary information to segment an album
            'message': 'What does the expected "hh:mm:ss" input represent?',
            'choices': choices,

        }
    ]
    answers = prompt(questions)
    return answers['how-to-input-tracks']


def interactive_track_info_input_dialog():
    print("Enter/Paste your 'track_name - hh:mm:ss' pairs. Each line should represent a single track with format 'trackname - hh:mm:ss'. "
          "The assumption is that each track is defined either in terms of a timestamp corrspoding to the starting point within the full album or its actuall playtime length. Then navigate one line below your last track and press Ctrl-D (or Ctrl-Z in $#*!% windows) to save it.\n")

    def input_lines(prompt_=None):
        """Yields input lines from user until EOFError is raised."""
        while True:
            try:
                yield input() if prompt_ is None else input(prompt_)
            except EOFError:
                break
            else:
                prompt_ = None  # Only display prompt while reading first line.

    def multiline_input(prompt_=None):
        """Reads a multi-line input from the user."""
        return os.linesep.join(input_lines(prompt_=prompt_))
    return multiline_input()  # '\n' separable string


####################################################################


##### STORE ALBUM DIALOG
def store_album_dialog(tracks, music_lib='', artist='', album='', year=''):

    def _copy_tracks(track_files, destination_dir):
        for track in track_files:
            destination_file_path = os.path.join(destination_dir, os.path.basename(track))
            if os.path.isfile(destination_file_path):
                print(" File '{}' already exists. in '{}'. Skipping".format(os.path.basename(track),
                                                                            destination_dir))
            else:
                shutil.copyfile(track, destination_file_path)
        print("Album tracks reside in '{}'".format(destination_dir))

    if year:
        album = '{} ({})'.format(album, year)
    else:
        album = album

    questions = [
        {
            'type': 'input',
            'name': 'create-album-dir',
            'message': 'Please give album directory path',
            'default': os.path.join(music_lib, artist, album),
            # 'when': lambda x: bool(not music_lib)
        },

    ]
    while 1:
        answers = prompt(questions)

        destination_directory = answers['create-album-dir']

        try:
            os.makedirs(destination_directory)
        except FileExistsError:
            ans = prompt([{'type': 'confirm',
                           'name': 'copy-in-existant-dir',
                           'message': "Directory '{}' exists. Copy the tracks there?".format(destination_directory),
                           'default': True}])
            if not ans['copy-in-existant-dir']:
                continue
        except FileNotFoundError:
            print("The selected destination directory '{}' is not valid.".format(destination_directory))
            continue
        except PermissionError:
            print("You don't have permision to create a directory in path '{}'".format(destination_directory))
            continue
        try:
            _copy_tracks(tracks, destination_directory)
            break
        except PermissionError:
            print("Can't copy tracks to '{}' folder. You don't have write permissions in this directory".format(destination_directory))
    return destination_directory


##### STORE METADATA DIALOGS
def interactive_metadata_dialogs(artist='', album='', year=''):
    class NumberValidator(Validator):
        def validate(self, document):
            if document.text != '':  # trick to allow empty value
                try:
                    int(document.text)
                except ValueError:
                    raise ValidationError(
                        message='Please enter a number',
                        cursor_position=len(document.text))  # Move cursor to end

    def set_metadata_panel(default_artist=artist, default_album=album, default_year=year):
        questions = [
            {
                'type': 'confirm',
                'name': 'add-metadata',
                'message': 'Do you want to add metadata, such as artist, track names, to the audio files?',
                'default': True,
            },
            {
                'type': 'checkbox',
                'name': 'automatic-metadata',
                'message': 'Infer from audio files',
                'when': lambda answers: bool(answers['add-metadata']),
                'choices': [
                    {
                        'name': 'track numbers',
                        'checked': True
                    },
                    {
                        'name': 'track names',
                        'checked': True
                    }
                ]
            },
            {
                'type': 'input',
                'name': 'artist',
                'default': default_artist,
                'message': "'artist' tag",
            },
            {
                'type': 'input',
                'name': 'album-artist',
                'message': "'album artist' tag",
                'default': lambda x: x['artist']
            },
            {
                'type': 'input',
                'name': 'album',
                'default': default_album,
                'message': "'album' tag",
            },
            {
                'type': 'input',
                'name': 'year',
                'message': "'year' tag",
                'default': default_year,  # trick to allow empty value
                'validate': NumberValidator,
                # 'filter': lambda val: int(val)
            },
        ]
        my_answers = prompt(questions)
        return my_answers

    return set_metadata_panel()
