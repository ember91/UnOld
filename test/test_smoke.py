import re
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import pytest

from unold import main


def test_unavailable_container_manager() -> None:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        main(['--container-manager', 'docker-podman', 'test/containerfiles/alpine.Containerfile'])

    assert stdout.getvalue() == ''
    assert stderr.getvalue() == "Container manager 'docker-podman' is not available\n"


def test_no_file_path_argument() -> None:
    stdout, stderr = StringIO(), StringIO()
    with pytest.raises(SystemExit), redirect_stdout(stdout), redirect_stderr(stderr):
        main([])

    assert stdout.getvalue() == ''
    assert (
        stderr.getvalue() == 'usage: Containerfile version checker [-h] [-c CONTAINER_MANAGER]\n'
        '                                     file_paths [file_paths ...]\n'
        'Containerfile version checker: error: the following arguments are required: file_paths\n'
    )


def test_non_buildable_containerfile() -> None:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        assert main(['test/containerfiles/alpine_doesnt_build.Containerfile']) == 1

    assert stdout.getvalue() == ''
    assert re.match(
        '/bin/sh: hfdjsk: not found\n'
        'Error: building at STEP "RUN hfdjsk": while running runtime: exit status 127\n'
        '\n'
        "Command '\\['podman', 'build', '-f', '/tmp/unold_.*?/unold_.*?', '-t', 'unold_.*?', '-q']' "
        'returned non-zero exit status 127.\n',
        stderr.getvalue(),
    )


def test_single_file() -> None:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        assert main(['test/containerfiles/alpine.Containerfile']) == 1

    assert stdout.getvalue() == ''
    assert re.match(
        "Package 'git' with version 2.43.0-r0 starting at line 3 in file 'test/containerfiles/alpine.Containerfile' "
        "is not up to date. The latest version is '.*?'.\n",
        stderr.getvalue(),
    )


def test_single_file_multi_stage() -> None:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        assert main(['test/containerfiles/alpine_multi_stage.Containerfile']) == 1

    assert stdout.getvalue() == ''
    assert (
        stderr.getvalue() == "Package 'git' with version 2.43.0-r0 starting at line 2 in file "
        "'test/containerfiles/alpine_multi_stage.Containerfile' is not up to date. The latest version is '2.45.2-r0'.\n"
        "Package 'nginx' with version 1.26.1-r0 starting at line 5 in file "
        "'test/containerfiles/alpine_multi_stage.Containerfile' is not up to date. The latest version is '1.26.2-r0'.\n"
    )
    assert re.match(
        "Package 'git' with version 2.43.0-r0 starting at line 2 in file "
        "'test/containerfiles/alpine_multi_stage.Containerfile' is not up to date. The latest version is '.*?'.\n"
        "Package 'nginx' with version 1.26.1-r0 starting at line 5 in file "
        "'test/containerfiles/alpine_multi_stage.Containerfile' is not up to date. The latest version is '.*?'.\n",
        stderr.getvalue(),
    )


def test_multiple_files() -> None:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        assert main(['test/containerfiles/alpine.Containerfile', 'test/containerfiles/ubuntu.Containerfile']) == 1

    assert stdout.getvalue() == ''
    assert re.match(
        "Package 'git' with version 2.43.0-r0 starting at line 3 in file 'test/containerfiles/alpine.Containerfile' "
        "is not up to date. The latest version is '.*?'.\n",
        stderr.getvalue(),
    )
