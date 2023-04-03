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
    return (
        YoutubeVideo(url, video_title)
        for url, video_title in [
            (
                'https://www.youtube.com/watch?v=jJkF3I5cBAc',
                '10 seconds countdown (video test)',
            ),
            (
                'https://www.youtube.com/watch?v=Q3dvbM6Pias',
                'Rage Against The Machine - Testify (Official HD Video)',
            ),
            (
                'https://www.youtube.com/watch?v=G95sOBFkRxs',
                'Legalize It',  # Cypress Hill 1080p HD 0:46
            ),
        ]
    )


@pytest.mark.network_bound("Makes a request to youtube.com, thus using network")
@pytest.mark.runner_setup(mix_stderr=False)
@mock.patch('music_album_creation.create_album.inout')
@mock.patch('music_album_creation.create_album.music_lib_directory')
def test_integration(
    mock_music_lib_directory,
    mock_inout,
    tmp_path_factory,
    isolated_cli_runner,
    valid_youtube_videos,
    get_object,
):
    download_dir = tmp_path_factory.mktemp('download_dir')

    assert os.listdir(download_dir) == []
    target_directory = str(tmp_path_factory.mktemp('temp-music-library'))

    mock_music_lib_directory.return_value = target_directory
    # GIVEN a youtube URL
    mock_inout.input_youtube_url_dialog.return_value = list(valid_youtube_videos)[2].url
    mock_inout.interactive_track_info_input_dialog.return_value = (
        '1.  Gasoline - 0:00\n' '2.  Man vs. God - 0:07\n'
    )
    expected_album_dir: str = os.path.join(target_directory, 'del/Faith_in_Science')
    mock_inout.track_information_type_dialog.return_value = 'Timestamps'
    mock_inout.album_directory_path_dialog.return_value = expected_album_dir
    user_input_metadata = {
        'artist': 'Test Artist',
        'album-artist': 'Test Artist',
        'album': 'Faith in Science',
        'year': '2019',
    }
    mock_inout.interactive_metadata_dialogs.return_value = user_input_metadata
    # Configure MusicMaster to download to our desired directory
    from music_album_creation.music_master import MusicMaster as MM

    def MusicMaster(*args, **kwargs):
        music_master = MM(*args, **kwargs)
        music_master.download_dir = download_dir
        return music_master

    # Monkey patch at the module level
    get_object(
        'main',
        'music_album_creation.create_album',
        overrides={'MusicMaster': lambda: MusicMaster},
    )

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

    # AND downloaded youtube video is found in the download directory
    assert len(os.listdir(download_dir)) == 1
    # AND the downloaded youtube file name is the expected
    print(os.listdir(download_dir))
    expected_file_name = 'Legalize It.mp4'
    assert os.listdir(download_dir)[0] == expected_file_name

    # READ downloaded stream file metadata to compare with segmented tracks
    from music_album_creation.ffmpeg import FFProbe
    from music_album_creation.ffprobe_client import FFProbeClient

    ffprobe = FFProbe(os.environ.get('MUSIC_FFPROBE', 'ffprobe'))
    ffprobe_client = FFProbeClient(ffprobe)

    BYTE_SIZE_ERROR_MARGIN = 0.01
    expected_bytes_size = 762505
    # download_dir
    downloaded_file = download_dir / expected_file_name
    # AND its metadata
    original_data = ffprobe_client.get_stream_info(str(downloaded_file))
    import json

    print(json.dumps(original_data, indent=4, sort_keys=True))
    # sanity check on metadata values BEFORE segmenting
    assert original_data['programs'] == []
    assert len(original_data['streams']) == 1

    assert original_data['streams'][0]['tags'] == {}
    # AND the audio stream has the expected Sample Rate (Hz)
    assert original_data['streams'][0]['sample_rate'] == '44100'

    # AND the audio stream has the expected codec
    assert original_data['streams'][0]['codec_name'] == 'aac'

    # AND the audio stream has the expected number of channels
    assert original_data['streams'][0]['channels'] == 2

    assert original_data['format']['format_name'] == 'mov,mp4,m4a,3gp,3g2,mj2'
    assert original_data['format']['format_long_name'] == 'QuickTime / MOV'
    assert original_data['format']['start_time'] == '-0.036281'
    assert original_data['format']['duration'] == '46.933333'
    assert original_data['format']['size'] == str(expected_bytes_size)
    assert downloaded_file.stat().st_size == expected_bytes_size
    assert original_data['format']['bit_rate'] == '129972'  # bits per second
    assert original_data['format']['probe_score'] == 100
    assert 'encoder' not in original_data['format']['tags']
    # assert original_data['format']['tags']['encoder'] == 'google/video-file'

    # AND the maths add up (size = track duration * bitrate)
    assert (
        int(original_data['format']['size'])
        >= 0.9
        * int(original_data['format']['bit_rate'])
        * float(original_data['format']['duration'])
        / 8
    )
    assert (
        int(original_data['format']['size'])
        <= 1.1
        * int(original_data['format']['bit_rate'])
        * float(original_data['format']['duration'])
        / 8
    )

    expected_durations = (7, 39)
    expected_sizes = (114010, 642005)  # in Bytes
    exp_bitrates = (129797, 128421)

    for track, expected_duration, expected_size, exp_bitrate in zip(
        sorted(list(expected_tracks)), expected_durations, expected_sizes, exp_bitrates
    ):
        # AND each track should have the expected metadata
        track_path = os.path.join(expected_album_dir, track)
        assert os.path.exists(track_path)

        # AND the track should have the expected size (within a window of error of 1%)
        assert abs(
            os.path.getsize(track_path) - expected_size
        ) <= BYTE_SIZE_ERROR_MARGIN * os.path.getsize(track_path)

        # assert os.path.getsize(track_path) == expected_size

        data = ffprobe_client.get_stream_info(track_path)
        import json

        # as reported by our metadata reading function
        track_byte_size = int(data['format']['size'])

        print(json.dumps(data, indent=4, sort_keys=True))
        assert data['programs'] == []
        assert len(data['streams']) == 1
        assert data['streams'][0]['tags'] == {}
        # AND the track file has the same stream quality as original  audio stream
        assert data['streams'][0]['sample_rate'] == '44100'
        assert data['streams'][0]['codec_name'] == 'mp3'
        assert data['streams'][0]['channels'] == 2
        assert data['format']['format_name'] == 'mp3'
        assert data['format']['format_long_name'] == 'MP2/3 (MPEG audio layer 2/3)'
        # assert data['format']['start_time'] == '-0.007000'
        assert abs(float(data['format']['duration']) - expected_duration) < 1
        # AND the track should have the expected size (within a window of error of 1%)
        assert abs(track_byte_size - expected_size) <= BYTE_SIZE_ERROR_MARGIN * track_byte_size

        reported_bitrate = int(data['format']['bit_rate'])
        # assert data['format']['bit_rate'] == str(exp_bitrate)  # bits per second
        assert abs(reported_bitrate - exp_bitrate) < 0.02 * reported_bitrate

        # assert data['format']['probe_score'] == 100
        assert data['format']['probe_score'] == 51
        assert data['format']['tags']['encoder'] == 'Lavf58.76.100'

        # AND maths add up (size = track duration * bitrate)
        estimated_size = (
            int(data['format']['bit_rate']) * float(data['format']['duration']) / 8
        )
        assert abs(int(data['format']['size']) - estimated_size) < 0.01 * estimated_size

        # AND bitrate has not changed more than 5% compared to original
        assert abs(
            int(data['format']['bit_rate']) - int(original_data['format']['bit_rate'])
        ) < 0.05 * int(original_data['format']['bit_rate'])

        # AND file size is proportional to duration (track byte size = track duration * bitrate)
        estimated_track_byte_size = (
            expected_bytes_size
            * expected_duration
            / float(original_data['format']['duration'])
        )
        assert (
            abs(int(data['format']['size']) - estimated_track_byte_size)
            < 0.05 * estimated_track_byte_size
        )

        # AND the artist tag is set to the expected artist
        assert data['format']['tags']['artist'] == user_input_metadata['artist']
        # AND the album_artist tag is set to the expected album_artist
        assert data['format']['tags']['album_artist'] == user_input_metadata['album-artist']
        # AND the album tag is set to the expected album
        assert data['format']['tags']['album'] == user_input_metadata['album']
        # AND the year tag is set to the expected year
        assert data['format']['tags']['date'] == user_input_metadata['year']
