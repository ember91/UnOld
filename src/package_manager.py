from __future__ import annotations

import argparse
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, override

from package import Package
from version import Version, VersionConditional

if TYPE_CHECKING:
    from collections.abc import Sequence


class PackageManager(ABC):
    def parse_install_package(self, command: Sequence[str]) -> list[tuple[list[Package], str]]:
        sub_cmd: list[str] = []
        packages_and_prefixes = []
        command_prefix = ''
        for i, s in enumerate(command):
            if s in {'&&', '||', ';'}:
                packages = self._parse_install_package_subcommand(sub_cmd)
                if packages:
                    packages_and_prefixes.append((packages, command_prefix))
                    command_prefix = ' '.join(command[:i])
                sub_cmd = []
                continue

            sub_cmd.append(s)

        if sub_cmd:
            packages = self._parse_install_package_subcommand(sub_cmd)
            if packages:
                packages_and_prefixes.append((packages, command_prefix))

        return packages_and_prefixes

    @abstractmethod
    def create_update_and_list_package_versions_command(self, package_names: Sequence[str]) -> str:
        raise NotImplementedError('Subclass this class and override this function')

    @abstractmethod
    def parse_version(self, package_version_str: str) -> Version | None:
        raise NotImplementedError('Subclass this class and override this function')

    @abstractmethod
    def parse_version_string(self, package_name: str, version_str: str) -> Version | None:
        raise NotImplementedError('Subclass this class and override this function')

    @abstractmethod
    def _parse_install_package_subcommand(self, command: Sequence[str]) -> list[Package]:
        raise NotImplementedError('Subclass this class and override this function')


class PackageManagerApk(PackageManager):
    @override
    def create_update_and_list_package_versions_command(self, package_names: Sequence[str]) -> str:
        if not package_names:
            raise RuntimeError('No package names supplied')
        return 'apk update -q && apk list ' + ' '.join(package_names)

    @override
    def parse_version(self, package_version_str: str) -> Version | None:
        spl = package_version_str.split(' ')
        if not spl:
            return None

        package_name, _, version_str = spl[0].partition('-')
        return self.parse_version_string(package_name, version_str)

    @override
    def parse_version_string(self, package_name: str, version_str: str) -> Version | None:
        match = re.match(r'([0-9]+)(\.([0-9]+)(\.([0-9]+)(-r([0-9]+))?)?)?', version_str)
        if not match:
            return None

        major, minor, patch, revision = None, None, None, None
        if match[1]:
            major = int(match[1])
        if match[3]:
            minor = int(match[3])
        if match[5]:
            patch = int(match[5])
        if match[7]:
            revision = int(match[7])
        return Version(
            package_name=package_name, source=version_str, major=major, minor=minor, patch=patch, revision=revision
        )

    @override
    def _parse_install_package_subcommand(self, command: Sequence[str]) -> list[Package]:
        try:
            apk_idx = command.index('apk')
        except ValueError:
            return []

        apk_args = command[apk_idx + 1 :]

        parser = argparse.ArgumentParser()
        parser_parent = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_add = subparsers.add_parser('add', parents=[parser_parent], add_help=False)

        # See:
        # - https://man.archlinux.org/man/extra/apk-tools/apk.8.en
        # - https://man.archlinux.org/man/extra/apk-tools/apk-add.8.en
        apk_args_with_values = [
            '--cache-dir',
            '--cache-max-age',
            '--keys-dir',
            '--progress-fd',
            '--repositories-file',
            '--repository',
            '--root',
            '--timeout',
            '--wait',
            '-p',
            '-X',
        ]
        apk_add_args_with_values = [
            '-t',
            '--virtual',
        ]

        for arg in apk_args_with_values:
            parser_parent.add_argument(arg)
        for arg in apk_add_args_with_values:
            parser_add.add_argument(arg)

        try:
            args_known, args_unknown = parser.parse_known_args(apk_args)
        except SystemExit:
            return []

        if args_known.command != 'add':
            return []

        return [PackageManagerApk._create_package(arg) for arg in args_unknown if not arg.startswith('-')]

    @staticmethod
    def _create_package(package_str: str) -> Package:
        name = None
        conditional = None
        version_str = None

        # Warning: Do not change the order here due to prefix rules
        if '==' in package_str:
            name, _, version_str = package_str.partition('==')
            conditional = VersionConditional.EQUALITY
        elif '=~' in package_str:
            name, _, version_str = package_str.partition('=~')
            conditional = VersionConditional.FUZZY
        elif '~=' in package_str:
            name, _, version_str = package_str.partition('~=')
            conditional = VersionConditional.FUZZY
        elif '<' in package_str:
            name, _, version_str = package_str.partition('<')
            conditional = VersionConditional.LESS_THAN
        elif '>' in package_str:
            name, _, version_str = package_str.partition('>')
            conditional = VersionConditional.GREATER_THAN
        elif '=' in package_str:
            name, _, version_str = package_str.partition('=')
            conditional = VersionConditional.EQUALITY
        elif '~' in package_str:
            name, _, version_str = package_str.partition('~')
            conditional = VersionConditional.FUZZY
        else:
            name = package_str
            conditional = VersionConditional.NONE

        return Package(name=name, conditional=conditional, version_str=version_str)
