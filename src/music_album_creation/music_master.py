import os
import shutil
import tempfile
from glob import glob

import attr

from .audio_segmentation import AudioSegmenter
from .downloading import CMDYoutubeDownloader
from .tracks_parsing import StringParser
from .web_parsing import video_title


@attr.s
class MusicMaster(object):
    music_library_path = attr.ib(init=True, repr=True)
    segmenter = attr.ib(init=False, factory=AudioSegmenter)
    youtube = attr.ib(init=False, factory=CMDYoutubeDownloader)
    download_dir = attr.ib(init=False, default=os.path.join(tempfile.gettempdir(), 'gav'))
    _mp3s = attr.ib(init=False, default={})

    def __attrs_post_init__(self):
        if os.path.isdir(self.download_dir):
            shutil.rmtree(self.download_dir)
        os.mkdir(self.download_dir)

    def update_youtube(self):
        self.youtube.update_backend()

    def url2mp3(self, url, suppress_certificate_validation=False, force_download=False):
        if force_download or url not in self._mp3s:
            self._download(
                url, suppress_certificate_validation=suppress_certificate_validation
            )
        return self._mp3s[url]

    def _download(self, url, suppress_certificate_validation=False):
        downloaded_mp3 = self.youtube.download_trials(
            url, self.download_dir, times=5, delay=0.5
        )
        latest_mp3 = downloaded_mp3
        # latest_mp3 = max(glob("{}/*.mp4".format(self.download_dir)), key=os.path.getctime)
        if os.path.basename(latest_mp3) == '_.mp3':
            self.guessed_info = StringParser().parse_album_info(video_title(url)[0])
            try:
                new_file = os.path.join(self.download_dir, self.guessed_info['artist'])
                os.rename(latest_mp3, new_file)
                self._mp3s[url] = new_file
            except KeyError as e:
                print(e)
                self._mp3s[url] = latest_mp3
        else:
            self.guessed_info = StringParser().parse_album_info(latest_mp3)
            self._mp3s[url] = latest_mp3
