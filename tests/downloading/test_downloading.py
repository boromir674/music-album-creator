import pytest

@pytest.fixture
def download_video():
    from music_album_creation.downloading import CMDYoutubeDownloader
    yd = CMDYoutubeDownloader()
    return yd.download_trials


@pytest.mark.network_bound
@pytest.mark.parametrize('url', [
    'https://www.youtube.com/watch?v=OvC-4BixxkY',
])
def test_downloading_audio_stream_without_specifying_output(url, tmp_path_factory, download_video):

    # GIVEN a youtube video url
    runtime_url: str = url

    # WHEN downloading the audio stream
    output_directory = tmp_path_factory.mktemp("youtubedownloads")
    TIMES = 3
    local_file = download_video(runtime_url, output_directory, times=TIMES)

    # THEN the audio stream is downloaded
    from pathlib import Path
    runtime_file = Path(local_file)
    assert runtime_file.exists()

    # AND the audio stream is saved in the output directory
    assert runtime_file.parent == output_directory

    # AND the audio stream has the expected name
    assert runtime_file.name == 'Burning.webm'
    # AND the audio stream has the expected extension
    assert runtime_file.suffix == '.webm'

    # AND the audio stream has the expected size
    expected_bytes_size = 6560225
    assert runtime_file.stat().st_size == expected_bytes_size  # 6.26 MB
    assert 6,256318092 - expected_bytes_size / 1024.0 / 1024.0 < 0.1
    """
    ffprobe -v error -show_entries stream_tags=rotate:format=size,duration:stream=codec_name,bit_rate -of default=noprint_wrappers=1 ./Burning.webm
    """
    from music_album_creation.ffmpeg import FFProbe
    from music_album_creation.ffprobe_client import FFProbeClient
    import os
    ffprobe = FFProbe(os.environ.get('MUSIC_FFPROBE', 'ffprobe'))
    ffprobe_client = FFProbeClient(ffprobe)

    # Query Media File to get metadata information
    data = ffprobe_client.get_stream_info(str(runtime_file))
    import json
    print(json.dumps(data, indent=4, sort_keys=True))

    assert data['programs'] == []
    assert len(data['streams']) == 1

    assert data['streams'][0]['tags'] == {}

    # AND the audio stream has the expected Sample Rate (Hz)
    assert data['streams'][0]['sample_rate'] == '48000'

    # AND the audio stream has the expected codec
    assert data['streams'][0]['codec_name'] == 'opus'

    # AND the audio stream has the expected number of channels
    assert data['streams'][0]['channels'] == 2

    assert data['format']['format_name'] == 'matroska,webm'
    assert data['format']['format_long_name'] == 'Matroska / WebM'
    assert data['format']['start_time'] == '-0.007000'
    assert data['format']['duration'] == '393.161000'
    assert data['format']['size'] == str(expected_bytes_size)
    assert data['format']['bit_rate'] == '133486'  # bits per second
    assert data['format']['probe_score'] == 100
    assert data['format']['tags']['encoder'] == 'google/video-file'   


@pytest.mark.network_bound
@pytest.mark.parametrize('url', [
    'https://www.youtube.com/watch?v=OvC-4BixxkY',
])
def test_downloading_audio_stream_specifying_mp3_output(url, tmp_path_factory):

    # GIVEN a youtube video url
    runtime_url: str = url

    # WHEN downloading the audio stream
    from pytube import YouTube
    output_directory = tmp_path_factory.mktemp("youtubedownloads")

    youtube_video = YouTube(runtime_url)
    try:
        title: str = youtube_video.title
    except Exception as error:
        print(error)
        title = 'Burning'

    highest_bitrate_audio_stream = youtube_video.streams.filter(only_audio=True).order_by('bitrate')[-1]

    local_file = highest_bitrate_audio_stream.download(
        output_path=str(output_directory),
        filename=f'{title}.mp3',
        filename_prefix=None,
        skip_existing=False,  # Skip existing files, defaults to True
        timeout=None,  # Request timeout length in seconds. Uses system default
        max_retries=0,  # Number of retries to attempt after socket timeout. Defaults to 0
    )

    # THEN the audio stream is downloaded
    from pathlib import Path
    runtime_file = Path(local_file)
    assert runtime_file.exists()

    # AND the audio stream is saved in the output directory
    assert runtime_file.parent == output_directory

    # AND the audio stream has the expected name
    assert runtime_file.name == 'Burning.mp3'
    # AND the audio stream has the expected extension
    assert runtime_file.suffix == '.mp3'


    # AND the audio stream has the expected size
    expected_bytes_size = 6560225
    assert runtime_file.stat().st_size == expected_bytes_size  # 6.26 MB
    assert 6,256318092 - expected_bytes_size / 1024.0 / 1024.0 < 0.1
    """
    ffprobe -v error -show_entries stream_tags=rotate:format=size,duration:stream=codec_name,bit_rate -of default=noprint_wrappers=1 ./Burning.webm
    """
    import subprocess

    # Query Media File to get metadata information
    cp = subprocess.run(  # pylint: disable=W1510
        ['ffprobe', '-v', 'error',
        '-show_entries', 'stream_tags=rotate:format=size,duration:stream=codec_name,bit_rate,sample_rate,channels,nb_frames',
        '-of', 'default=noprint_wrappers=1', str(runtime_file)],
        capture_output=True,  # capture stdout and stderr separately
        # cwd=project_directory,
        check=True,
    )

    res: str = str(cp.stdout, encoding='utf-8')
    print(res)
    data = dict(x.split('=') for x in res.strip().split('\n'))

    # AND size reported by ffprobe is the same
    assert data['size'] == str(expected_bytes_size)

    # AND the audio stream has the expected duration
    assert data['duration'] == '393.161000'

    # AND the audio stream has the expected Sample Rate (Hz)
    assert data['sample_rate'] == '48000'

    # AND the audio stream has the expected codec
    assert data['codec_name'] == 'opus'

    # AND the audio stream has the expected bitrate
    assert data['bit_rate'] == 'N/A'

    # AND the audio stream has the expected number of channels
    assert data['channels'] == '2'

    # AND the audio stream has the expected number of frames
    assert data['nb_frames'] == 'N/A'
