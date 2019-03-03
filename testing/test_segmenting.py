import os
import pytest
import mutagen

from album_segmentation import AudioSegmenter, Timestamp, TrackTimestampsSequenceError, WrongTimestampFormat

this_dir = os.path.dirname(os.path.realpath(__file__))

@pytest.fixture(scope='module')
def test_audio_file_path():
    return os.path.join(this_dir, 'Know Your Enemy.mp3')

segmenter = AudioSegmenter()


dur = '4:56'

class TestSegmenting:

    def test_illogical_timetamp_sequence(self, tmpdir, test_audio_file_path):
        with pytest.raises(TrackTimestampsSequenceError):
            segmenter.target_directory = str(tmpdir.mkdir('album'))
            segmenter.segment_from_list(test_audio_file_path, [['t1', '0:00'], ['t2', '1:00'], ['t3', '0:35']], supress_stdout=True, verbose=False, sleep_seconds=0)

    def test_wrong_timestamp_input(self, tmpdir, test_audio_file_path):
        with pytest.raises(WrongTimestampFormat):
            segmenter.target_directory = str(tmpdir.mkdir('album'))
            segmenter.segment_from_list(test_audio_file_path, [['t1', '0:00'], ['t2', '1:a0'], ['t3', '1:35']], supress_stdout=True, verbose=False, sleep_seconds=0)

    @pytest.mark.parametrize("tracks, names, durations", [
        ("1. tr1 - 0:00\n2. tr2 - 1:12\n3. tr3 - 2:00\n", ['01 - tr1.mp3','02 - tr2.mp3','03 - tr3.mp3'], [72, 48, 236]),
        pytest.param("1. tr1 - 0:00\n2. tr2 - 1:12\n3. tr3 - 1:00\n",
                     ['01 - tr1.mp3','02 - tr2.mp3','03 - tr3.mp3'],
                     [72, 48, 236], marks=pytest.mark.xfail),
        pytest.param("1. tr1 - 0:00\n2. tr2 - 1:72\n3. tr3 - 3:00\n",
                     ['01 - tr1.mp3', '02 - tr2.mp3', '03 - tr3.mp3'],
                     [72, 48, 236], marks=pytest.mark.xfail),
    ])
    def test_valid_segmentation0(self, tracks, names, durations, tmpdir, test_audio_file_path):
        segmenter.target_directory = str(tmpdir.mkdir('album'))
        tracks_file = tmpdir.join('tracks.txt')
        tracks_file.write_text(tracks, 'utf-8')
        segmenter.segment_from_file(test_audio_file_path, str(tracks_file), supress_stdout=True, verbose=False, sleep_seconds=0)
        file_names = sorted(os.listdir(segmenter.target_directory))
        assert file_names == names
        assert [abs(getattr(mutagen.File(os.path.join(segmenter.target_directory, x[0])).info, 'length', 0) - x[1]) < 1 for x in zip(file_names, durations)]
