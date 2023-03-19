import os
import subprocess

from unittest import mock
import pytest
from click.testing import CliRunner
from music_album_creation.create_album import main


class TestCreateAlbum:
    def test_executable(self):
        assert subprocess.call(['create-album', '--help']) == 0


@pytest.fixture(scope='module')
def integration_data():
    return "Music library: /media/kostas/freeagent/m\nLogo\n"


@pytest.mark.network_bound("Makes a request to youtube.com, thus using network")
@pytest.mark.runner_setup(mix_stderr=False)
@mock.patch('music_album_creation.create_album.inout')
@mock.patch('music_album_creation.create_album.music_lib_directory')
def test_integration(mock_music_lib_directory, mock_inout, tmpdir, isolated_cli_runner, valid_youtube_videos):
    target_directory = str(tmpdir.mkdir('temp-music-library'))

    mock_music_lib_directory.return_value = target_directory
    mock_inout.input_youtube_url_dialog.return_value = list(valid_youtube_videos)[0].url
    mock_inout.interactive_track_info_input_dialog.return_value = \
        '1.  Gasoline - 0:00\n' \
        '2.  Man vs. God - 0:07\n'
    mock_inout.track_information_type_dialog.return_value = 'Timestamps'
    mock_inout.album_directory_path_dialog.return_value = os.path.join(target_directory, 'del/Faith_in_Science')
    mock_inout.interactive_metadata_dialogs.return_value = {'artist': 'del', 'album-artist': 'del', 'album': 'Faith in Science', 'year': '2019'}

    result = isolated_cli_runner.invoke(
        main,
        args=None,
        input=None,
        env=None,
        catch_exceptions=False,
        color=False,
        **{},
    )
    print(result.stdout)
    print(result.stderr)
    assert result.stderr == ''
    assert result.exit_code == 0
    print("CAP\n{}\nCAP".format(result.output))
    # captured = capsys.readouterr()
