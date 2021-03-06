"""Sanity checks for command-line options."""
import re
from subprocess import PIPE
from subprocess import Popen

import pytest


@pytest.fixture
def current_version():
    return open('VERSION').read().strip()


def test_no_arguments_prints_usage(both_debug_modes, both_setsid_modes):
    proc = Popen(('dumb-init'), stderr=PIPE)
    _, stderr = proc.communicate()
    assert proc.returncode != 0
    assert stderr == (
        b'Usage: dumb-init [option] program [args]\n'
        b'Try dumb-init --help for full usage.\n'
    )


@pytest.mark.parametrize('flag', ['-h', '--help'])
def test_help_message(flag, both_debug_modes, both_setsid_modes, current_version):
    """dumb-init should say something useful when called with the help flag,
    and exit zero.
    """
    proc = Popen(('dumb-init', flag), stderr=PIPE)
    _, stderr = proc.communicate()
    assert proc.returncode == 0
    assert stderr == (
        b'dumb-init v' + current_version.encode('ascii') + b'\n'
        b'Usage: dumb-init [option] command [[arg] ...]\n'
        b'\n'
        b'dumb-init is a simple process supervisor that forwards signals to children.\n'
        b'It is designed to run as PID1 in minimal container environments.\n'
        b'\n'
        b'Optional arguments:\n'
        b'   -c, --single-child   Run in single-child mode.\n'
        b'                        In this mode, signals are only proxied to the\n'
        b'                        direct child and not any of its descendants.\n'
        b'   -r, --rewrite s:r    Rewrite received signal s to new signal r before proxying.\n'
        b'                        To ignore (not proxy) a signal, rewrite it to 0.\n'
        b'                        This option can be specified multiple times.\n'
        b'   -v, --verbose        Print debugging information to stderr.\n'
        b'   -h, --help           Print this help message and exit.\n'
        b'   -V, --version        Print the current version and exit.\n'
        b'\n'
        b'Full help is available online at https://github.com/Yelp/dumb-init\n'
    )


@pytest.mark.parametrize('flag', ['-V', '--version'])
def test_version_message(flag, both_debug_modes, both_setsid_modes, current_version):
    """dumb-init should print its version when asked to."""

    proc = Popen(('dumb-init', flag), stderr=PIPE)
    _, stderr = proc.communicate()
    assert proc.returncode == 0
    assert stderr == b'dumb-init v' + current_version.encode('ascii') + b'\n'


@pytest.mark.parametrize('flag', ['-v', '--verbose'])
def test_verbose(flag):
    """dumb-init should print debug output when asked to."""
    proc = Popen(('dumb-init', flag, 'echo', 'oh,', 'hi'), stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    assert proc.returncode == 0
    assert stdout == b'oh, hi\n'
    assert re.match(
        (
            b'^\[dumb-init\] Child spawned with PID [0-9]+\.\n'
            b'\[dumb-init\] setsid complete\.\n'
            b'\[dumb-init\] Received signal 17\.\n'
            b'\[dumb-init\] A child with PID [0-9]+ exited with exit status 0.\n'
            b'\[dumb-init\] Forwarded signal 15 to children\.\n'
            b'\[dumb-init\] Child exited with status 0\. Goodbye\.\n$'
        ),
        stderr,
    )


@pytest.mark.parametrize('flag1', ['-v', '--verbose'])
@pytest.mark.parametrize('flag2', ['-c', '--single-child'])
def test_verbose_and_single_child(flag1, flag2):
    """dumb-init should print debug output when asked to."""
    proc = Popen(('dumb-init', flag1, flag2, 'echo', 'oh,', 'hi'), stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    assert proc.returncode == 0
    assert stdout == b'oh, hi\n'
    assert re.match(
        (
            b'^\[dumb-init\] Child spawned with PID [0-9]+\.\n'
            b'\[dumb-init\] Received signal 17\.\n'
            b'\[dumb-init\] A child with PID [0-9]+ exited with exit status 0.\n'
            b'\[dumb-init\] Forwarded signal 15 to children\.\n'
            b'\[dumb-init\] Child exited with status 0\. Goodbye\.\n$'
        ),
        stderr,
    )


@pytest.mark.parametrize('extra_args', [
    ('-r',),
    ('-r', ''),
    ('-r', 'herp'),
    ('-r', 'herp:derp'),
    ('-r', '15'),
    ('-r', '15::12'),
    ('-r', '15:derp'),
    ('-r', '15:12', '-r'),
    ('-r', '15:12', '-r', '0'),
    ('-r', '15:12', '-r', '1:32'),
])
@pytest.mark.usefixtures('both_debug_modes', 'both_setsid_modes')
def test_rewrite_errors(extra_args):
    proc = Popen(
        ('dumb-init',) + extra_args + ('echo', 'oh,', 'hi'),
        stdout=PIPE, stderr=PIPE,
    )
    stdout, stderr = proc.communicate()
    assert proc.returncode == 1
    assert stderr == (
        b'Usage: -r option takes <signum>:<signum>, where <signum> '
        b'is between 1 and 31.\n'
        b'This option can be specified multiple times.\n'
        b'Use --help for full usage.\n'
    )
