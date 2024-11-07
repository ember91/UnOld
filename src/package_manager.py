from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from package import Package
    from version import Version


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
