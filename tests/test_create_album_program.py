import os
import subprocess

import mock
import pytest
from click.testing import CliRunner

from music_album_creation.create_album import main


class TestCreateAlbum:

    def test_launching(self):
        ro = subprocess.run(['create-album', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert ro.returncode == 0

@pytest.fixture(scope='module')
def integration_data():
    return "Music library: /media/kostas/freeagent/m\nLogo\n"

@mock.patch('music_album_creation.create_album.inout')
@mock.patch('music_album_creation.create_album.music_lib_directory')
def test_integration(mock_music_lib_directory, mock_inout, tmpdir, integration_data):
    target_directory = str(tmpdir.mkdir('temp-music-library'))
    runner = CliRunner()
    mock_music_lib_directory.return_value = target_directory
    mock_inout.input_youtube_url_dialog.return_value = 'https://www.youtube.com/watch?v=Wjrrgrvq1ew'
    mock_inout.interactive_track_info_input_dialog.return_value = \
        '1.  Gasoline - 0:00\n' \
        '2.  Man vs. God - 0:10\n'
    mock_inout.track_information_type_dialog.return_value = 'Timestamps'
    mock_inout.album_directory_path_dialog.return_value = os.path.join(target_directory, 'del/Faith_in_Science')
    mock_inout.interactive_metadata_dialogs.return_value = {'artist': 'del', 'album-artist': 'del', 'album': 'Faith in Science', 'year': '2019'}

    result = runner.invoke(main, [])
    print("CAP\n{}\nCAP".format(result.output))
    # captured = capsys.readouterr()
    assert result.exit_code == 0
