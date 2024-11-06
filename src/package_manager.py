from __future__ import annotations

import argparse
import re
from abc import ABC, abstractmethod
from contextlib import redirect_stderr
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, override

from package import Package
from version import Version, VersionConditional

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class ParseInstallPackageResult:
    packages: list[Package]
    forwarded_args: list[str]
    command_prefix: str


class PackageManager(ABC):
    def parse_install_package(self, command: Sequence[str]) -> list[ParseInstallPackageResult]:
        sub_cmd: list[str] = []
        results = []
        command_prefix = ''
        for i, s in enumerate(command):
            if s in {'&&', '||', ';'}:
                packages, forwarded_args = self._parse_install_package_subcommand(sub_cmd)
                if packages:
                    results.append(ParseInstallPackageResult(packages, forwarded_args, command_prefix))
                    command_prefix = ' '.join(command[:i])
                sub_cmd = []
                continue

            sub_cmd.append(s)

        if sub_cmd:
            packages, forwarded_args = self._parse_install_package_subcommand(sub_cmd)
            if packages:
                results.append(ParseInstallPackageResult(packages, forwarded_args, command_prefix))

        return results

    @abstractmethod
    def create_query_versions_command(self, package_names: Sequence[str], forward_arguments: Sequence[str]) -> str:
        raise NotImplementedError('Subclass this class and override this function')

    @abstractmethod
    def parse_version(self, package_version_str: str) -> Version | None:
        raise NotImplementedError('Subclass this class and override this function')

    @abstractmethod
    def parse_version_string(self, package_name: str, version_str: str) -> Version | None:
        raise NotImplementedError('Subclass this class and override this function')

    @abstractmethod
    def _parse_install_package_subcommand(self, command: Sequence[str]) -> tuple[list[Package], list[str]]:
        raise NotImplementedError('Subclass this class and override this function')


class PackageManagerApk(PackageManager):
    @override
    def create_query_versions_command(self, package_names: Sequence[str], forward_arguments: Sequence[str]) -> str:
        if not package_names:
            raise RuntimeError('No package names supplied')

        all_args = list(forward_arguments) + list(package_names)
        return 'apk update -q && apk list ' + ' '.join(all_args)

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
    def _parse_install_package_subcommand(self, command: Sequence[str]) -> tuple[list[Package], list[str]]:
        try:
            apk_idx = command.index('apk')
        except ValueError:
            return [], []

        apk_args = command[apk_idx + 1 :]

        parser = argparse.ArgumentParser()
        parser_parent = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_add = subparsers.add_parser('add', parents=[parser_parent], add_help=False)

        # See:
        # - https://man.archlinux.org/man/extra/apk-tools/apk.8.en
        # - https://man.archlinux.org/man/extra/apk-tools/apk-add.8.en
        apk_args_with_values = [
            '--arch',
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
            # Hide stderr output from argparse
            with redirect_stderr(StringIO()):
                args_parent_known, _ = parser_parent.parse_known_args(apk_args)
                args_known, args_unknown = parser.parse_known_args(apk_args)
        except SystemExit:
            return [], []

        if args_known.command != 'add':
            return [], []

        forwarded_args = []
        if args_parent_known.arch:
            forwarded_args.extend(['--arch', args_parent_known.arch])
        if args_parent_known.repository:
            forwarded_args.extend(['--repository', args_parent_known.repository])
        if args_parent_known.X:
            forwarded_args.extend(['-X', args_parent_known.X])

        return [
            PackageManagerApk._create_package(arg) for arg in args_unknown if not arg.startswith('-')
        ], forwarded_args

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
