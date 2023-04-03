import json
from typing import Any, Dict, Protocol

from attr import define


class CLIResult(Protocol):
    exit_code: int
    stdout: str
    stderr: str


class FFProbeCallable(Protocol):
    def __call__(self, *args: str) -> CLIResult:
        ...


@define
class FFProbeClient:
    ffprobe: FFProbeCallable

    def get_stream_info(self, file_path: str) -> Dict[str, Any]:
        cli_result = self.ffprobe(
            '-v',
            'error',
            '-show_entries',
            'stream_tags=rotate:format=size,duration:stream=codec_name,bit_rate,sample_rate,channels,nb_frames',
            '-of',
            'default=noprint_wrappers=1',
            '-show_format',
            '-print_format',
            'json',
            str(file_path),
        )
        if cli_result.exit_code != 0:
            raise RuntimeError(f"ffprobe failed with exit code {cli_result.exit_code}")
        assert cli_result.exit_code == 0
        assert cli_result.stderr == ''
        res = cli_result.stdout
        return json.loads(res)
