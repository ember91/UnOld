from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class VersionComparison(Enum):
    UNCOMPARABLE = auto()
    LESS_THAN_OTHER = auto()
    EQUAL = auto()
    GREATER_THAN_OTHER = auto()


class VersionConditional(Enum):
    NONE = auto()
    LESS_THAN = auto()
    EQUALITY = auto()
    GREATER_THAN = auto()
    FUZZY = auto()


@dataclass(frozen=True)
class Version:
    source: str
    package_name: str
    major: int | None = None
    minor: int | None = None
    patch: int | None = None
    revision: int | None = None

    def compare(self, other: Version) -> VersionComparison:
        tup_mine: tuple = ()
        tup_other: tuple = ()
        for element_mine, element_other in zip(
            (self.major, self.minor, self.patch, self.revision),
            (other.major, other.minor, other.patch, other.revision),
            strict=True,
        ):
            if element_mine is None or element_other is None:
                break

            tup_mine += (element_mine,)
            tup_other += (element_other,)

        if not tup_mine or not tup_other:
            return VersionComparison.UNCOMPARABLE
        if tup_mine < tup_other:
            return VersionComparison.LESS_THAN_OTHER
        if tup_mine == tup_other:
            return VersionComparison.EQUAL
        return VersionComparison.GREATER_THAN_OTHER
