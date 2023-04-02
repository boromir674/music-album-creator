import os
from unittest import mock

import pytest

from music_album_creation.create_album import main


def test_invoking_cli_with_help_flag(run_subprocess):
    """Smoke test to ensure that the CLI can be invoked with the help flag"""
    import sys
    result = run_subprocess(
        sys.executable,
        '-m',
        'music_album_creation',
        '--help',
        check=False,  # we disable check, because we do it in unit test below
    )
    assert result.stderr == ''
    assert result.exit_code == 0


@pytest.fixture
def valid_youtube_videos():
    """Youtube video urls and their expected mp3 name to be 'downloaded'.

    Note:
        Maintain this fixture in cases such as a youtube video title changing
        over time, or a youtube url ceasing to exist.

    Returns:
        [type]: [description]
    """
    from collections import namedtuple

    YoutubeVideo = namedtuple('YoutubeVideo', ['url', 'video_title'])
    return {
        YoutubeVideo(url, video_title)
        for url, video_title in {
            (
                'https://www.youtube.com/watch?v=jJkF3I5cBAc',
                '10 seconds countdown (video test)',
            ),
            (
                'https://www.youtube.com/watch?v=Q3dvbM6Pias',
                'Rage Against The Machine - Testify (Official HD Video)'
            ),
        }
    }


@pytest.mark.network_bound("Makes a request to youtube.com, thus using network")
@pytest.mark.runner_setup(mix_stderr=False)
@mock.patch('music_album_creation.create_album.inout')
@mock.patch('music_album_creation.create_album.music_lib_directory')
def test_integration(
    mock_music_lib_directory, mock_inout, tmpdir, isolated_cli_runner, valid_youtube_videos
):
    target_directory = str(tmpdir.mkdir('temp-music-library'))

    mock_music_lib_directory.return_value = target_directory
    mock_inout.input_youtube_url_dialog.return_value = list(valid_youtube_videos)[1].url
    mock_inout.interactive_track_info_input_dialog.return_value = (
        '1.  Gasoline - 0:00\n' '2.  Man vs. God - 0:07\n'
    )
    expected_album_dir: str = os.path.join(
        target_directory, 'del/Faith_in_Science'
    )
    mock_inout.track_information_type_dialog.return_value = 'Timestamps'
    mock_inout.album_directory_path_dialog.return_value = expected_album_dir
    mock_inout.interactive_metadata_dialogs.return_value = {
        'artist': 'del',
        'album-artist': 'del',
        'album': 'Faith in Science',
        'year': '2019',
    }

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

    # AND the album directory should be created
    assert os.path.isdir(expected_album_dir)

    # AND the album directory should contain the expected tracks
    expected_tracks = {
        '01 - Gasoline.mp3',
        '02 - Man vs. God.mp3',
    }
    assert set(os.listdir(expected_album_dir)) == expected_tracks

    # AND the tracks should be encoded as mp3

    # AND the tracks should have the expected metadata

    # AND the tracks should have the expected duration

    # AND the tracks should have the expected filesize

    # AND the tracks should have the expected bitrate

    # AND the tracks should have the expected sample rate

    # AND the tracks should have the expected channels

