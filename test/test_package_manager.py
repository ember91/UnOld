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
    def create_query_versions_command(self, package_names: Sequence[str], forward_arguments: Sequence[str]) -> str:
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
    results = pkg_man.parse_install_package([])
    assert results == []


def test_parse_install_package_single(pkg_man: PackageManagerStub) -> None:
    results = pkg_man.parse_install_package(['apk', 'add', 'git=2.43.0'])
    assert len(results) == 1
    assert results[0].packages == [Package('apk'), Package('add'), Package('git=2.43.0')]
    assert results[0].forwarded_args == ['-X', 'repo']
    assert results[0].command_prefix == ''


def test_parse_install_package_trailing_semicolon(pkg_man: PackageManagerStub) -> None:
    results = pkg_man.parse_install_package(['apk', 'add', 'git=2.43.0', ';'])
    assert len(results) == 1
    assert results[0].packages == [Package('apk'), Package('add'), Package('git=2.43.0')]
    assert results[0].forwarded_args == ['-X', 'repo']
    assert results[0].command_prefix == ''


def test_parse_install_package_multi(pkg_man: PackageManagerStub) -> None:
    results = pkg_man.parse_install_package(
        ['apk', 'update', '&&', 'apk', 'add', 'git=2.43.0', '||', 'ls', ';', 'rm', '-rf', '/var/cache/apk/*']
    )
    assert len(results) == 4
    assert results[0].packages == [Package('apk'), Package('update')]
    assert results[0].forwarded_args == ['-X', 'repo']
    assert results[0].command_prefix == ''
    assert results[1].packages == [Package('apk'), Package('add'), Package('git=2.43.0')]
    assert results[1].forwarded_args == ['-X', 'repo']
    assert results[1].command_prefix == 'apk update'
    assert results[2].packages == [Package('ls')]
    assert results[2].forwarded_args == ['-X', 'repo']
    assert results[2].command_prefix == 'apk update && apk add git=2.43.0'
    assert results[3].packages == [Package('rm'), Package('-rf'), Package('/var/cache/apk/*')]
    assert results[3].forwarded_args == ['-X', 'repo']
    assert results[3].command_prefix == 'apk update && apk add git=2.43.0 || ls'
