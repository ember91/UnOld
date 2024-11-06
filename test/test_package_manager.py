from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from package import Package
from package_manager import PackageManager

if TYPE_CHECKING:
    from collections.abc import Sequence

    from version import Version


class PackageManagerStub(PackageManager):
    @override
    def create_update_and_list_package_versions_command(
        self, package_names: Sequence[str], forward_arguments: list[str]
    ) -> str:
        raise NotImplementedError

    @override
    def parse_version(self, package_version_str: str) -> Version | None:
        raise NotImplementedError

    @override
    def parse_version_string(self, package_name: str, version_str: str) -> Version | None:
        raise NotImplementedError

    @override
    def _parse_install_package_subcommand(self, command: Sequence[str]) -> tuple[list[Package], list[str]]:
        return [Package(s) for s in command], ['-X', 'repo']


@pytest.fixture
def pkg_man() -> PackageManagerStub:
    return PackageManagerStub()


def test_parse_install_package_empty(pkg_man: PackageManagerStub) -> None:
    packages_forwards_prefixes = pkg_man.parse_install_package([])
    assert packages_forwards_prefixes == []


def test_parse_install_package_single(pkg_man: PackageManagerStub) -> None:
    packages_forwards_prefixes = pkg_man.parse_install_package(['apk', 'add', 'git=2.43.0'])
    assert len(packages_forwards_prefixes) == 1
    packages, forwards, command_prefix = packages_forwards_prefixes[0]
    assert packages == [Package('apk'), Package('add'), Package('git=2.43.0')]
    assert forwards == ['-X', 'repo']
    assert command_prefix == ''


def test_parse_install_package_trailing_semicolon(pkg_man: PackageManagerStub) -> None:
    packages_forwards_prefixes = pkg_man.parse_install_package(['apk', 'add', 'git=2.43.0', ';'])
    assert len(packages_forwards_prefixes) == 1
    packages, forwards, command_prefix = packages_forwards_prefixes[0]
    assert packages == [Package('apk'), Package('add'), Package('git=2.43.0')]
    assert forwards == ['-X', 'repo']
    assert command_prefix == ''


def test_parse_install_package_multi(pkg_man: PackageManagerStub) -> None:
    packages_forwards_prefixes = pkg_man.parse_install_package(
        ['apk', 'update', '&&', 'apk', 'add', 'git=2.43.0', '||', 'ls', ';', 'rm', '-rf', '/var/cache/apk/*']
    )
    assert len(packages_forwards_prefixes) == 4
    packages, forwards, command_prefix = packages_forwards_prefixes[0]
    assert packages == [Package('apk'), Package('update')]
    assert forwards == ['-X', 'repo']
    assert command_prefix == ''
    packages, forwards, command_prefix = packages_forwards_prefixes[1]
    assert packages == [Package('apk'), Package('add'), Package('git=2.43.0')]
    assert forwards == ['-X', 'repo']
    assert command_prefix == 'apk update'
    packages, forwards, command_prefix = packages_forwards_prefixes[2]
    assert packages == [Package('ls')]
    assert forwards == ['-X', 'repo']
    assert command_prefix == 'apk update && apk add git=2.43.0'
    packages, forwards, command_prefix = packages_forwards_prefixes[3]
    assert packages == [Package('rm'), Package('-rf'), Package('/var/cache/apk/*')]
    assert forwards == ['-X', 'repo']
    assert command_prefix == 'apk update && apk add git=2.43.0 || ls'
