from .ffprobe_proxy import FFProbeProxy
from .ffprobe_subject import FFProbeSubject

__all__ = ['FFProbeProxy']


# Proxy that proxies a Singleton ffprobe instance
class FFProbe(FFProbeProxy):
    def __init__(self, ffprobe_binary: str):
        super().__init__(FFProbeSubject(ffprobe_binary))
