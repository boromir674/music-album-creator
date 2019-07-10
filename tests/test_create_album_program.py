
import subprocess

from click.testing import CliRunner

from music_album_creation.create_album import main


class TestCreateAlbum:

    def test_launching(self):
        ro = subprocess.run(['create-album', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert ro.returncode == 0

    def test_main(self):
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
