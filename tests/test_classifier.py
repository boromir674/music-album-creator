import pytest

from music_album_creation.format_classification import dataset_handler, FormatClassifier


model = "src/music_album_creation/format_classification/data/model.pickle"


@pytest.fixture(scope='module')
def format_classifier():
    return FormatClassifier.load(model)


class TestClassifier:

    def test_evaluation_on_blind_set(self, format_classifier):
        feature_vectors, labels = dataset_handler.load_dataset_split('test')
        assert 0.98 < format_classifier.score(feature_vectors, labels)
