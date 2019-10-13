import os
import sys

from PyInquirer import ValidationError, Validator, prompt

# __all__ = ['store_album_dialog', 'interactive_metadata_dialogs']


class InputFactory:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
            if sys.version_info.major == 2:
                cls.__instance._input = raw_input  # NOQA
            else:
                cls.__instance._input = input
        return cls.__instance

    def __call__(self, *args):
        return self._input(*args)


ask_input = InputFactory()


class DialogCommander:

    @classmethod
    def logo(cls):
        print(
            "\
╔═╗╦  ╔╗ ╦ ╦╔╦╗  ╔═╗╦═╗╔═╗╔═╗╔╦╗╔═╗╦═╗\n\
╠═╣║  ╠╩╗║ ║║║║  ║  ╠╦╝║╣ ╠═╣ ║ ║ ║╠╦╝\n\
╩ ╩╩═╝╚═╝╚═╝╩ ╩  ╚═╝╩╚═╚═╝╩ ╩ ╩ ╚═╝╩╚═\
            ")

    @classmethod
    def print(cls, string):
        print(string)

    @classmethod
    def input_youtube_url_dialog(cls):
        """"""
        return ask_input('Please input a url corresponding to a music album uploaded as a youtube video.\n   video url: ')


    ## HANDLE Token Error with update youtube-dl and retry download same url dialog
    @classmethod
    def update_and_retry_dialog(cls):
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
    @classmethod
    def track_information_type_dialog(cls, prediction=''):
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

    @classmethod
    def interactive_track_info_input_dialog(cls):
        print("Enter/Paste your 'track_name - hh:mm:ss' pairs. Each line should represent a single track with format 'trackname - hh:mm:ss'. "
              "The assumption is that each track is defined either in terms of a timestamp corrspoding to the starting point within the full album or its actuall playtime length. Then navigate one line below your last track and press Ctrl-D (or Ctrl-Z in $#*!% windows) to save it.\n")

        def input_lines(prompt_=None):
            """Yields input lines from user until EOFError is raised."""
            while True:
                try:
                    yield ask_input() if prompt_ is None else ask_input(prompt_)
                except EOFError:
                    break
                else:
                    prompt_ = None  # Only display prompt while reading first line.

        def multiline_input(prompt_=None):
            """Reads a multi-line input from the user."""
            return os.linesep.join(input_lines(prompt_=prompt_))
        return multiline_input()  # '\n' separable string


    ####################################################################

    @classmethod
    def album_directory_path_dialog(cls, music_lib, artist='', album='', year=''):
        if year:
            album = '{} ({})'.format(album, year)
        else:
            album = album
        return prompt([{'type': 'input',
                        'name': 'create-album-dir',
                        'message': 'Please give album directory path',
                        'default': os.path.join(music_lib, artist, album)}])['create-album-dir']

    @classmethod
    def confirm_copy_tracks_dialog(cls, destination_directory):
        return prompt([{'type': 'confirm',
                        'name': 'copy-in-existant-dir',
                        'message': "Directory '{}' exists. Copy the tracks there?".format(destination_directory),
                        'default': True}])['copy-in-existant-dir']

    @classmethod
    def interactive_metadata_dialogs(cls, artist='', album='', year=''):
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
                'default': artist,
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
                'default': album,
                'message': "'album' tag",
            },
            {
                'type': 'input',
                'name': 'year',
                'message': "'year' tag",
                'default': year,  # trick to allow empty value
                'validate': NumberValidator,
                # 'filter': lambda val: int(val)
            },
        ]
        return prompt(questions)


class NumberValidator(Validator):
    def validate(self, document):
        if document.text != '':  # trick to allow empty value
            try:
                int(document.text)
            except ValueError:
                raise ValidationError(
                    message='Please enter a number',
                    cursor_position=len(document.text))  # Move cursor to end
