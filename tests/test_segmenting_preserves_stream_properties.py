
def test_segmenting_webm_preserves_stream_qualities(tmp_path_factory):
    from typing import List
    import os
    from pathlib import Path
    from music_album_creation.ffmpeg import FFProbe
    from music_album_creation.ffprobe_client import FFProbeClient
    from music_album_creation.audio_segmentation import AudioSegmenter
    ffprobe = FFProbe(os.environ.get('MUSIC_FFPROBE', 'ffprobe'))
    ffprobe_client = FFProbeClient(ffprobe)

    expected_bytes_size = 6560225

    # GIVEN a webm file
    webm_file = Path(__file__).parent / 'data' / 'Burning.webm'
    # AND its metadata
    original_data = ffprobe_client.get_stream_info(str(webm_file))
    # sanity check on metadata values BEFORE segmenting
    assert original_data['programs'] == []
    assert len(original_data['streams']) == 1

    assert original_data['streams'][0]['tags'] == {}
    # AND the audio stream has the expected Sample Rate (Hz)
    assert original_data['streams'][0]['sample_rate'] == '48000'

    # AND the audio stream has the expected codec
    assert original_data['streams'][0]['codec_name'] == 'opus'

    # AND the audio stream has the expected number of channels
    assert original_data['streams'][0]['channels'] == 2

    assert original_data['format']['format_name'] == 'matroska,webm'
    assert original_data['format']['format_long_name'] == 'Matroska / WebM'
    assert original_data['format']['start_time'] == '-0.007000'
    assert original_data['format']['duration'] == '393.161000'
    assert original_data['format']['size'] == str(expected_bytes_size)
    assert webm_file.stat().st_size == expected_bytes_size
    assert original_data['format']['bit_rate'] == '133486'  # bits per second
    assert original_data['format']['probe_score'] == 100
    assert original_data['format']['tags']['encoder'] == 'google/video-file'

    # AND maths add up (size = track duration * bitrate)
    assert int(original_data['format']['size']) >= 0.9 * int(original_data['format']['bit_rate']) * float(original_data['format']['duration']) / 8
    assert int(original_data['format']['size']) <= 1.1 * int(original_data['format']['bit_rate']) * float(original_data['format']['duration']) / 8


    # WHEN segmenting the webm file
    output_dir = tmp_path_factory.mktemp("segmented")
    segmenter = AudioSegmenter(str(output_dir))
    track_files: List[str] = segmenter.segment(str(webm_file), (
        ('1 - track1', '0', '10'),
        ('2 - track2', '10', '15'),
    ))
    # THEN the webm file is segmented
    assert len(track_files) == 2

    # AND the webm file is segmented into segments with the expected duration

    expected_durations = (10, 5)
    expected_sizes = (160749, 80877)  # in Bytes
    exp_bitrates = (128188, 128376)
    for track, expected_duration, expected_size, exp_bitrate in zip(track_files, expected_durations, expected_sizes, exp_bitrates):
        assert os.path.exists(track)
        data = ffprobe_client.get_stream_info(track)

        assert data['programs'] == []
        assert len(data['streams']) == 1
        assert data['streams'][0]['tags'] == {}
        # AND the track file has the same stream quality as original  audio stream
        assert data['streams'][0]['sample_rate'] == '48000'
        assert data['streams'][0]['codec_name'] == 'mp3'
        assert data['streams'][0]['channels'] == 2
        assert data['format']['format_name'] == 'mp3'
        assert data['format']['format_long_name'] == 'MP2/3 (MPEG audio layer 2/3)'
        # assert data['format']['start_time'] == '-0.007000'
        assert abs( float(data['format']['duration']) - expected_duration ) < 0.1
        assert int(data['format']['size']) == expected_size
        assert data['format']['bit_rate'] == str(exp_bitrate)  # bits per second
        # assert data['format']['probe_score'] == 100
        assert data['format']['probe_score'] == 51
        assert data['format']['tags']['encoder'] == 'Lavf58.76.100'

        # AND maths add up (size = track duration * bitrate)
        estimated_size = int(data['format']['bit_rate']) * float(data['format']['duration']) / 8
        assert abs( int(data['format']['size']) - estimated_size ) < 0.01 * estimated_size

        # AND bitrate has not changed more than 5% compared to original
        assert abs( int(data['format']['bit_rate']) - int(original_data['format']['bit_rate']) ) < 0.05 * int(original_data['format']['bit_rate'])

        # AND file size is proportional to duration (track byte size = track duration * bitrate)
        estimated_track_byte_size = expected_bytes_size * expected_duration / float(original_data['format']['duration'])
        assert abs( int(data['format']['size']) - estimated_track_byte_size ) < 0.05 * estimated_track_byte_size
