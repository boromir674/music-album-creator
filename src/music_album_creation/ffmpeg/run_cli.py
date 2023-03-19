import subprocess
import sys


class CLIResult:
    """Wrap the subprocess.CompletedProcess class to make it easier to use."""

    def __init__(self, completed_process: subprocess.CompletedProcess):
        self._exit_code = int(completed_process.returncode)
        self._stdout = str(completed_process.stdout, encoding='utf-8')
        self._stderr = str(completed_process.stderr, encoding='utf-8')

    @property
    def exit_code(self) -> int:
        return self._exit_code

    @property
    def stdout(self) -> str:
        return self._stdout

    @property
    def stderr(self) -> str:
        return self._stderr


SUBPROCESS_RUN_MAP = {
    True: {  # legacy python <= 3.6
        'stdout': subprocess.PIPE,  # capture stdout and stderr separately
        'stderr': subprocess.PIPE,
        'check': True,
    },
    False: {  # python > 3.6
        'capture_output': True,  # capture stdout and stderr separately
        'check': True,
    },
}


def execute_command_in_subprocess(
    executable: str, *cli_args, **subprocess_settings
) -> CLIResult:
    """Execute a command in a subprocess and return the result.

    The subprocess is implicitly not allowed to raise an exception in case the process exits
    with a non-zero exit code.
    It is left to the client to check the 'exit_code' property and decide how to handle it.

    Args:
        executable (str): path to executable program/binary (ie a CLI)
        *cli_args (str): arguments to pass to the executable
        **subprocess_settings: keyword arguments to pass to subprocess.run (check=False is always set)

    Returns:
        CLIResult: a wrapper around the subprocess.CompletedProcess class
    """

    def subprocess_run() -> CLIResult:
        kwargs_dict = SUBPROCESS_RUN_MAP[sys.version_info < (3, 7)]
        completed_process = subprocess.run(  # pylint: disable=W1510
            [executable] + list(cli_args),
            **dict(dict(kwargs_dict, **subprocess_settings), check=False)
        )
        return CLIResult(completed_process)

    return subprocess_run()
