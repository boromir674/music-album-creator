from .ffmpeg_proxy import FFMPEGProxy
from .ffmpeg_subject import FFMPEGSubject


# Singleton ffmpeg binary
class FFMPEG(FFMPEGProxy):
    def __init__(self, ffmpeg_binary: str):
        super().__init__(FFMPEGSubject(ffmpeg_binary))
