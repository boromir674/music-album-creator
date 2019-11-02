from music_album_creation.dialogs import ask_input


def test_ask_input():
    assert hasattr(ask_input, '_input')
    assert type(ask_input._input).__name__ == 'builtin_function_or_method'
