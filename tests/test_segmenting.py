import os
import pytest
import mutagen

from music_album_creation.album_segmentation import AudioSegmenter, NotStartingFromZeroTimestampError
from music_album_creation.tracks_parsing import WrongTimestampFormat, TrackTimestampsSequenceError


this_dir = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture(scope='module')
def test_audio_file_path():
    return os.path.join(this_dir, 'know_your_enemy.mp3')


segmenter = AudioSegmenter()


class TestSegmenting:

    def test_input_durations_to_segment(self, tmpdir, test_audio_file_path):
        durations_data = [['t1', '0:10'], ['t2', '0:40'], ['t3', '0:10']]

        with pytest.raises(NotStartingFromZeroTimestampError, match=r"First track \({}\) is supposed to have a 0:00 timestamp. Instead {} found".format(durations_data[0][0], durations_data[0][1])):
            segmenter.target_directory = str(tmpdir.mkdir('album'))
            segmenter.segment_from_list(test_audio_file_path, durations_data)

    def test_illogical_timetamp_sequence(self, tmpdir, test_audio_file_path):
        with pytest.raises(TrackTimestampsSequenceError):
            segmenter.target_directory = str(tmpdir.mkdir('album'))
            segmenter.segment_from_list(test_audio_file_path, [['t1', '0:00'], ['t2', '1:00'], ['t3', '0:35']], supress_stdout=True, verbose=False, sleep_seconds=0)

    def test_wrong_timestamp_input(self, tmpdir, test_audio_file_path):
        with pytest.raises(WrongTimestampFormat):
            segmenter.target_directory = str(tmpdir.mkdir('album'))
            segmenter.segment_from_list(test_audio_file_path, [['t1', '0:00'], ['t2', '1:a0'], ['t3', '1:35']], supress_stdout=True, verbose=False, sleep_seconds=0)

    @pytest.mark.parametrize("tracks, names, durations", [
        ("1. tr1 - 0:00\n2. tr2 - 1:12\n3. tr3 - 2:00\n", ['01 - tr1.mp3', '02 - tr2.mp3', '03 - tr3.mp3'], [72, 48, 236]),
        pytest.param("1. tr1 - 0:00\n2. tr2 - 1:12\n3. tr3 - 1:00\n",
                     ['01 - tr1.mp3', '02 - tr2.mp3', '03 - tr3.mp3'],
                     [72, 48, 236], marks=pytest.mark.xfail),
        pytest.param("1. tr1 - 0:00\n2. tr2 - 1:72\n3. tr3 - 3:00\n",
                     ['01 - tr1.mp3', '02 - tr2.mp3', '03 - tr3.mp3'],
                     [72, 48, 236], marks=pytest.mark.xfail),
    ])
    def test_valid_segmentation(self, tracks, names, durations, tmpdir, test_audio_file_path):
        segmenter.target_directory = str(tmpdir.mkdir('album'))
        tracks_file = tmpdir.join('tracks.txt')
        tracks_file.write_text(tracks, 'utf-8')
        segmenter.segment_from_file(test_audio_file_path, str(tracks_file), supress_stdout=False, supress_stderr=False, verbose=False, sleep_seconds=0)
        file_names = sorted(os.listdir(segmenter.target_directory))
        assert file_names == names
        assert [abs(getattr(mutagen.File(os.path.join(segmenter.target_directory, x[0])).info, 'length', 0) - x[1]) < 1 for x in zip(file_names, durations)]
