from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import Enum, auto
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
    class State(Enum):
        NOT_IN_APK = auto()
        IN_APK = auto()
        IN_APK_ADD = auto()
        IN_APK_ADD_FLAG = auto()

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
        arguments_with_values = {'-t', '--virtual'}

        packages = []

        state = PackageManagerApk.State.NOT_IN_APK
        for s in command:
            # TODO: Use match-case in Python3.10
            if state == PackageManagerApk.State.NOT_IN_APK:
                if s == 'apk':
                    state = PackageManagerApk.State.IN_APK
            elif state == PackageManagerApk.State.IN_APK:
                if s == 'add':
                    state = PackageManagerApk.State.IN_APK_ADD
            elif state == PackageManagerApk.State.IN_APK_ADD:
                if s.startswith('-'):
                    if s in arguments_with_values:
                        state = PackageManagerApk.State.IN_APK_ADD_FLAG
                else:
                    packages.append(PackageManagerApk._create_package(s))
            elif state == PackageManagerApk.State.IN_APK_ADD_FLAG:
                state = PackageManagerApk.State.IN_APK_ADD
            else:
                raise RuntimeError(f'Unexpected state {state}')

        return packages

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
