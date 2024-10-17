from textwrap import dedent

from unold import generate_containerfile_contents


def test_no_command_prefix() -> None:
    output = generate_containerfile_contents(
        dedent("""
        FROM alpine:3.20

        RUN apk add --no-cache \
            git==2.43.0-r0 \
            nginx==1.26.2-r0
        """),
        'some_command',
        3,
        '',
    )
    assert output == dedent("""
        FROM alpine:3.20

        CMD some_command
""")


def test_with_command_prefix() -> None:
    output = generate_containerfile_contents(
        dedent("""
        FROM alpine:3.20

        RUN apk add --no-cache \
            git==2.43.0-r0 \
            nginx==1.26.2-r0
        """),
        'some_command',
        3,
        'command_prefix',
    )
    assert output == dedent("""
        FROM alpine:3.20

        CMD command_prefix && some_command
""")
