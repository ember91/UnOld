from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import nox

if TYPE_CHECKING:
    from collections.abc import Sequence


# Usage examples:
# * Run all: 'nox'
# * Only linting: 'nox -t lint'
# * Only one function: 'nox -e flake8'

PYTHON_VERSION = '3.12'

nox.options.reuse_existing_virtualenvs = True


def install(session: nox.Session) -> None:
    session.install('-r', 'requirements_dev.txt')


def files(*args, exclude: Sequence[str] | None = None) -> list[str]:
    exclude_set = set() if exclude is None else set(exclude)
    list_ = set(subprocess.check_output(['git', 'ls-files', '-z', *args], text=True).strip('\0').split('\0'))
    return list(list_.difference(exclude_set))


@nox.session(tags=['fix'])
def black(session: nox.Session) -> None:
    install(session)
    session.run(
        'black',
        *session.posargs,
        *files('*.py'),
        external=True,
    )


@nox.session(tags=['lint'])
def hadolint(session: nox.Session) -> None:
    install(session)
    session.run('hadolint', *session.posargs, *files('*.Containerfile'), external=True)


@nox.session(tags=['lint'])
def mypy(session: nox.Session) -> None:
    install(session)
    session.run('mypy', *session.posargs, *files('*.py'), external=True)


@nox.session(tags=['format'])
def prettier_format(session: nox.Session) -> None:
    install(session)
    session.run(
        'npx',
        'prettier',
        '--config',
        '.prettierrc.json',
        '-w',
        *session.posargs,
        *files('*.md', '*.json', '*.yaml', '*.yml'),
        external=True,
    )


@nox.session(tags=['lint'])
def prettier_lint(session: nox.Session) -> None:
    install(session)
    session.run(
        'npx',
        'prettier',
        '--config',
        '.prettierrc.json',
        '-l',
        *session.posargs,
        *files('*.md', '*.json', '*.yaml', '*.yml'),
        external=True,
    )


@nox.session(python=PYTHON_VERSION, tags=['test'])
def pytest(session: nox.Session) -> None:
    install(session)
    session.run('pytest', *session.posargs)


@nox.session(python=PYTHON_VERSION, tags=['fix'])
def ruff_fix(session: nox.Session) -> None:
    install(session)
    session.run('ruff', 'check', '--fix', *session.posargs, *files('*.py'))


@nox.session(python=PYTHON_VERSION, tags=['format'])
def ruff_format(session: nox.Session) -> None:
    install(session)
    session.run('ruff', 'format', *session.posargs, *files('*.py'))
    session.run('ruff', 'check', '--fix', '--select', 'I', *session.posargs, *files('*.py'))


@nox.session(python=PYTHON_VERSION, tags=['lint'])
def ruff_lint(session: nox.Session) -> None:
    install(session)
    session.run('ruff', 'check', *session.posargs, *files('*.py'))


@nox.session(python=PYTHON_VERSION, tags=['lint'])
def ruff_lint_format(session: nox.Session) -> None:
    install(session)
    session.run('ruff', 'format', '--check', *session.posargs, *files('*.py'))


@nox.session(tags=['lint'])
def shellcheck(session: nox.Session) -> None:
    session.run('shellcheck', *session.posargs, *files('*.sh'), external=True)


@nox.session(tags=['fix'])
def shfmt_fix(session: nox.Session) -> None:
    install(session)
    session.run('shfmt', '-i', '4', '-s', '-w', *session.posargs, *files('*.sh'), external=True)


@nox.session(tags=['format'])
def shfmt_format(session: nox.Session) -> None:
    install(session)
    session.run('shfmt', '-i', '4', '-w', *session.posargs, *files('*.sh'), external=True)


@nox.session(tags=['lint'])
def shfmt_lint(session: nox.Session) -> None:
    install(session)
    session.run('shfmt', '-i', '4', '-d', *session.posargs, *files('*.sh'), external=True)


@nox.session(python=PYTHON_VERSION, tags=['lint'])
def typos(session: nox.Session) -> None:
    install(session)
    session.run(
        'typos',
        '--config',
        'typos.toml',
        '--force-exclude',
        *session.posargs,
        *files(
            '*.bat',
            '*.c',
            '*.cc',
            '*.cpp',
            '*.css',
            '*.h',
            '*.js',
            '*.json',
            '*.code-workspace',
            '*.html',
            '*.md',
            '*.py',
            '*.sh',
            '*.toml',
            '*.txt',
            '*.yaml',
            '*.yml',
        ),
    )


def _sync_vale() -> None:
    path_hash = Path('vale.hash')
    path_ini = Path('vale.ini')

    ini_contents = path_ini.read_text(encoding='utf-8')
    hash_ini = hashlib.sha1(ini_contents.encode()).hexdigest()

    do_sync = False
    try:
        hash_cached = path_hash.read_text(encoding='utf-8').strip()
        if hash_ini != hash_cached:
            do_sync = True
    except OSError:
        do_sync = True

    if do_sync:
        subprocess.check_call(['vale', 'sync'])
        path_hash.write_text(hash_ini, encoding='utf-8')


@nox.session(tags=['lint'])
def vale(session: nox.Session) -> None:
    install(session)

    _sync_vale()
    session.run('vale', *session.posargs, *files('*.md', exclude=['todo.md']), external=True)


@nox.session(python=PYTHON_VERSION, tags=['lint'])
def vulture(session: nox.Session) -> None:
    install(session)
    session.run('vulture', '--config', 'pyproject.toml', *session.posargs, *files('*.py'))
