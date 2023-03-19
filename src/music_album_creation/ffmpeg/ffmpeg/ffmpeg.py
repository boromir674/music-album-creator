"""FFMpeg as a Proxy to a Singleton instance using subprocess and ffmpeg CLI.

Audio options:
-aframes number     set the number of audio frames to output
-aq quality         set audio quality (codec-specific)
-ar rate            set audio sampling rate (in Hz)
-ac channels        set number of audio channels
-an                 disable audio
-acodec codec       force audio codec ('copy' to copy stream)
-vol volume         change audio volume (256=normal)
-af filter_graph    set audio filters
"""
from .ffmpeg_proxy import FFMPEGProxy
from .ffmpeg_subject import FFMPEGSubject


# Singleton ffmpeg binary
class FFMPEG(FFMPEGProxy):
    def __init__(self, ffmpeg_binary: str):
        super().__init__(FFMPEGSubject(ffmpeg_binary))
