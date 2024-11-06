#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING

import dockerfile  # type: ignore[import-not-found]

from install_location import InstallLocation
from package_manager import PackageManager, PackageManagerApk
from version import Version, VersionComparison, VersionConditional

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(args_cmd_line: Sequence[str] | None = None) -> int:
    args = parse_arguments(args_cmd_line)
    container_manager = args.container_manager
    file_paths = [Path(path_str) for path_str in args.file_paths]

    if not is_command_available(container_manager):
        print(f"Container manager '{container_manager}' is not available", file=sys.stderr)
        return 1

    exit_code = 0

    for file_path in file_paths:
        try:
            if not check_file(container_manager, file_path):
                exit_code = 1
        # Keep running even if we have one error
        # ruff: noqa: BLE001,PERF203
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            exit_code = 1

    return exit_code


def parse_arguments(args_cmd_line: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='Containerfile version checker',
        description='Check if containerfiles (such as dockerfiles) have up to date packages',
    )

    # TODO: Change this default from podman to docker
    parser.add_argument(
        '-c',
        '--container-manager',
        default='podman',
        help=(
            'Container manager, such as podman or docker. Ensure that either it is available in $PATH or pass its '
            'absolute path.'
        ),
    )
    parser.add_argument('file_paths', nargs='+', help='Containerfile paths')
    return parser.parse_args(args_cmd_line)


def is_command_available(command: str) -> bool:
    return which(command) is not None


def check_file(container_manager: str, file_path: Path) -> bool:
    success = True

    package_manager = PackageManagerApk()  # TODO

    containerfile_contents = file_path.read_text(encoding='utf-8')
    layers = parse_containerfile_contents(containerfile_contents)

    install_locations = read_packages(layers, package_manager, file_path)
    for install_location in install_locations:
        for package in install_location.packages:
            package.version = package_manager.parse_version_string(package.name, package.version_str)

    with tempfile.TemporaryDirectory(prefix='unold_') as dir_tmp_str:
        dir_tmp_path = Path(dir_tmp_str)
        for install_location in install_locations:
            if not check_install_location(install_location, container_manager, containerfile_contents, dir_tmp_path):
                success = False

    return success


def parse_containerfile_contents(contents: str) -> tuple[dockerfile.Command, ...]:
    return dockerfile.parse_string(contents)


def read_packages(
    layers: tuple[dockerfile.Command, ...],
    package_manager: PackageManager,
    file_path: Path,
) -> list[InstallLocation]:
    install_locations: list[InstallLocation] = []
    for layer in layers:
        if layer.cmd.casefold() == 'run'.casefold():
            command = shlex.split(layer.value[0])
            parse_install_package_results = package_manager.parse_install_package(command)
            install_locations.extend(
                InstallLocation(
                    result.packages,
                    file_path,
                    layer.start_line - 1,
                    package_manager,
                    result.forwarded_args,
                    result.command_prefix,
                )
                for result in parse_install_package_results
            )
    return install_locations


def check_install_location(
    install_location: InstallLocation, container_manager: str, containerfile_contents: str, dir_path: Path
) -> bool:
    package_manager = PackageManagerApk()  # TODO

    package_names = [package.name for package in install_location.packages]
    package_str = package_manager.create_query_versions_command(package_names, install_location.argument_forwards)
    version_query_containerfile = generate_containerfile_contents(
        containerfile_contents,
        package_str,
        install_location.containerfile_start_line,
        install_location.command_prefix,
    )

    image_name = generate_image_name(version_query_containerfile)

    build_image(container_manager, version_query_containerfile, dir_path, image_name)
    results = run_container_from_image(container_manager, image_name)
    version_strings = results.splitlines()
    packages_and_versions = parse_versions(version_strings, package_manager)
    return compare_versions(install_location, packages_and_versions)


def generate_containerfile_contents(input_: str, package_str: str, break_line: int, command_prefix: str) -> str:
    lines = input_.splitlines()
    lines = lines[:break_line]

    line = 'CMD '
    if command_prefix:
        line += f'{command_prefix} && '
    line += package_str
    lines.append(line)
    return '\n'.join(lines) + '\n'


def generate_image_name(str_: str) -> str:
    # Famous last words: 16^8 = 2^32 bits hash should be sufficient
    hash_ = hashlib.sha1(str_.encode()).hexdigest()[:8]
    return f'unold_{hash_}'


def build_image(container_manager: str, containerfile_contents: str, dir_: Path, image_name: str) -> None:
    file_path = Path(dir_ / image_name)
    file_path.write_text(containerfile_contents, encoding='utf-8')
    try:
        subprocess.check_output(
            [container_manager, 'build', '-f', str(file_path), '-t', image_name, '-q'],
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr, file=sys.stderr)
        raise


def run_container_from_image(container_manager: str, image_name: str) -> str:
    return subprocess.check_output([container_manager, 'run', image_name], text=True).strip()


def parse_versions(version_strings: Sequence[str], package_manager: PackageManager) -> dict[str, Version]:
    packages_and_versions = {}
    for version_string in version_strings:
        version = package_manager.parse_version(version_string)
        if version:
            packages_and_versions[version.package_name] = version

    return packages_and_versions


def compare_versions(
    install_location: InstallLocation,
    packages_and_versions: dict[str, Version],
) -> bool:
    success = True

    for package in install_location.packages:
        try:
            version_newest = packages_and_versions[package.name]
        except KeyError:
            print(
                f"Failed to find version of package '{package.name}' starting at line "
                f"{install_location.containerfile_start_line + 1} in file '{install_location.containerfile_path}'",
                file=sys.stderr,
            )
            success = False
            continue
        comparison = package.version.compare(version_newest)
        if (
            package.conditional in {VersionConditional.EQUALITY, VersionConditional.FUZZY}
            and comparison != VersionComparison.EQUAL
        ):
            print(
                f"Package '{package.name}' with version {package.version.source} starting at line "
                f"{install_location.containerfile_start_line + 1} in file '{install_location.containerfile_path}' is "
                f"not up to date. The latest version is '{version_newest.source}'.",
                file=sys.stderr,
            )
            success = False

    return success


if __name__ == '__main__':
    sys.exit(main())
