from dataclasses import dataclass
from pathlib import Path

from package import Package
from package_manager import PackageManager


@dataclass(frozen=True)
class InstallLocation:
    packages: list[Package]
    containerfile_path: Path
    containerfile_start_line: int  # Zero indexed
    package_manager: PackageManager
    command_prefix: str
