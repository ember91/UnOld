from __future__ import annotations

from dataclasses import dataclass

from version import Version, VersionConditional


@dataclass
class Package:
    name: str
    conditional: VersionConditional = VersionConditional.NONE
    version_str: str | None = None
    version: Version | None = None
