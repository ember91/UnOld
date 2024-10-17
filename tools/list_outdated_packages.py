#!/usr/bin/env python3

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from tabulate import tabulate

# TODO: When supported use 'uv list --outdated' over pip


async def exec_async(*args) -> str:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode().strip()
    stderr = stderr_bytes.decode().strip()
    return_code = process.returncode

    if isinstance(return_code, int) and return_code != 0:
        raise subprocess.CalledProcessError(return_code, str(args), stdout, stderr)

    return stdout


async def main() -> int:
    args = _parse_arguments()
    top_dir = Path(await exec_async('git', 'rev-parse', '--show-toplevel'))

    if args.requirements:
        requirements_paths = [Path(path_str) for path_str in args.requirements]
    else:
        requirements_paths = [top_dir / 'requirements_dev.txt']

    version_major, version_minor = sys.version_info[0:2]  # TODO: This should be Python3.9 though
    cmd_py = f'python{version_major}.{version_minor}'
    cmd_pip = f'pip{version_major}.{version_minor}'

    outdated_results = await asyncio.gather(
        *[_get_outdated(cmd_py, cmd_pip, requirements_path) for requirements_path in requirements_paths]
    )
    for outdated, requirements_path in zip(outdated_results, requirements_paths):
        _present(outdated, requirements_path)

    return 0 if sum(len(outdated) for outdated in outdated_results) == 0 else 1


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='List outdated Python packages')
    parser.add_argument(
        '-r',
        '--requirements',
        nargs='*',
        help="Path to Python pip Requirements file to scan. This is often called something along 'requirements.txt'.",
    )
    return parser.parse_args()


async def _get_outdated(cmd_py: str, cmd_pip: str, requirements_path: Path) -> list[dict[str, str]]:
    with tempfile.TemporaryDirectory() as dir_tmp_str:
        dir_tmp = Path(dir_tmp_str)
        dir_venv = dir_tmp / '.venv'
        venv_pip = dir_venv / 'bin' / cmd_pip
        venv_uv = dir_venv / 'bin' / 'uv'

        await exec_async(cmd_py, '-m', 'venv', str(dir_venv))
        await exec_async(str(venv_pip), 'install', 'uv', '--upgrade', 'pip', '-q')
        await exec_async(str(venv_uv), 'pip', 'install', '-r', str(requirements_path), '-q')
        outdated_str = await exec_async(str(venv_pip), 'list', '--outdated', '--format', 'json')

    return json.loads(outdated_str)


def _present(outdated: Sequence[dict[str, str]], requirements_path: Path) -> None:
    if not outdated:
        print(f"No outdated packages in '{requirements_path}'")
        return

    table = [[element['name'], element['version'], element['latest_version']] for element in outdated]

    print(f"Outdated packages in '{requirements_path}':", file=sys.stderr)
    print(
        tabulate(
            table,
            headers=['Name', 'Current', 'Latest'],
            tablefmt='psql',
        ),
        file=sys.stderr,
    )


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
