from textwrap import dedent

import dockerfile  # type: ignore[import-not-found]
import pytest

from unold import parse_containerfile_contents

# Just a sanity test. I'm not going to test the library that much.


def test_valid() -> None:
    contents = dedent("""
    FROM alpine:3.20

    RUN apk add --no-cache \
        git==2.43.0-r0 \
        nginx==1.26.2-r0""")

    command = parse_containerfile_contents(contents)

    assert len(command) == 2

    cmd_from, cmd_run = command

    assert cmd_from.cmd == 'FROM'
    assert cmd_from.sub_cmd is None
    assert cmd_from.json is False
    assert cmd_from.original == 'FROM alpine:3.20'
    assert cmd_from.start_line == 2
    assert cmd_from.flags == ()
    assert cmd_from.value == ('alpine:3.20',)

    assert cmd_run.cmd == 'RUN'
    assert cmd_run.sub_cmd is None
    assert cmd_run.json is False
    assert cmd_run.original == 'RUN apk add --no-cache         git==2.43.0-r0         nginx==1.26.2-r0'
    assert cmd_run.start_line == 4
    assert cmd_run.flags == ()
    assert cmd_run.value == ('apk add --no-cache         git==2.43.0-r0         nginx==1.26.2-r0',)


def test_invalid() -> None:
    contents = dedent("""
    FROM ubuntu:xenial\n

    # hadolint ignore=DL3025
    CMD ["echo", 1]\n
                      """)

    with pytest.raises(dockerfile.GoParseError):
        parse_containerfile_contents(contents)
